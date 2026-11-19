"""
lark_inspector.py —— 公共巡检模块（放在 common/ 目录下）

用法：
    from common.lark_inspector import run_inspection

    def check_xxx():
        response = requests.post(...)
        assert response.status_code == 200, "..."
        data = response.json()["data"]
        assert data["xxx"] == "...", "..."
        return {"订单号": data["orderNo"], "成交价": data["dealPrice"]}

    if __name__ == "__main__":
        run_inspection("订单查询", check_xxx)

配置：
    Webhook 地址从项目根目录的 .env 文件读取，.env 里加一行：
        LARK_WEBHOOK_URL=https://open.feishu.cn/open-apis/bot/v2/hook/xxxxxxxx

【本次修复】：之前手动编辑时把 send_lark_message 的 is_error 参数语义写反了
（红绿颜色靠两处反向巧合抵消，能正常显示，但语义是错的，容易在后续修改时踩坑）。
这一版恢复正确语义：is_error=True -> 红色告警，is_error=False -> 绿色正常。
"""

import os
import traceback
from datetime import datetime
import requests

from common.logger import logger
from configs.settings import PROJECT_ROOT  # ensures project .env is loaded


LARK_WEBHOOK_URL = os.getenv("LARK_WEBHOOK_URL")  # 从环境变量里读取飞书 webhook 地址

# 是否在用例通过时也发消息（False = 只在失败时告警，群里更清净）
NOTIFY_ON_SUCCESS = os.getenv("LARK_NOTIFY_ON_SUCCESS", "true").lower() == "true"


def send_lark_message(title: str, content: str, is_error: bool = False):
    """
    发送飞书卡片消息。
    is_error=True  -> 红色卡片（告警）
    is_error=False -> 绿色卡片（正常，默认值）
    """
    if not LARK_WEBHOOK_URL:
        logger.warning("未配置 LARK_WEBHOOK_URL，跳过飞书通知。请在 .env 里加一行 LARK_WEBHOOK_URL=你的webhook地址")
        return

    payload = {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {"tag": "plain_text", "content": title},
                "template": "red" if is_error else "green",
            },
            "elements": [
                {"tag": "div", "text": {"tag": "lark_md", "content": content}}
            ],
        },
    }
    try:
        resp = requests.post(LARK_WEBHOOK_URL, json=payload, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        logger.error(f"发送飞书消息时出错: {e}")


def run_inspection(name: str, check_func) -> bool:
    """
    统一的巡检执行入口。

    name: 用例名称（比如"订单查询"），用于消息标题
    check_func: 一个无参数函数，内部自己完成请求 + 断言。
                - 断言失败要 raise AssertionError（正常写法用 assert 就行）
                - 成功时返回一个 dict，作为展示信息（可以为空 dict）

    返回 True/False，表示这次巡检是否通过。
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        info = check_func() or {}
        detail_lines = "\n".join(f"**{k}**：{v}" for k, v in info.items())
        content = (
            f"**巡检时间**：{now}\n"
            f"**用例**：{name}\n"
            f"{detail_lines}\n"
            f"**结果**：✅ 通过"
        )
        if NOTIFY_ON_SUCCESS:
            send_lark_message(f"✅ {name} 巡检正常", content, is_error=False)
        logger.info(f"✅ {name} 巡检通过")
        return True

    except AssertionError as e:
        content = (
            f"**巡检时间**：{now}\n"
            f"**用例**：{name}\n"
            f"**失败原因**：断言失败 - {e}"
        )
        send_lark_message(f"🚨 {name} 巡检告警", content, is_error=True)
        logger.error(f"❌ {name} 断言失败: {e}")
        return False

    except Exception as e:
        short_trace = traceback.format_exc()[-500:]
        content = (
            f"**巡检时间**：{now}\n"
            f"**用例**：{name}\n"
            f"**失败原因**：请求/解析异常 - {e}\n"
            f"```\n{short_trace}\n```"
        )
        send_lark_message(f"🚨 {name} 巡检告警", content, is_error=True)
        logger.error(f"❌ {name} 请求异常: {e}")
        return False

def send_pytest_summary(passed: int, failed: int, skipped: int, duration: float,business_directory: str = "未识别"):
    """
    发送 Pytest 执行结果汇总通知。

    单文件执行：发送该文件的执行结果
    目录批量执行：发送整个目录的执行结果

    复用 send_lark_message，不重复定义卡片模板。
    """
    total = passed + failed + skipped

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if failed > 0:
        result = "❌ 执行失败"
        is_error = True
    else:
        result = "✅ 执行成功"
        is_error = False

    content = (
        f"**执行时间**：{now}\n"
        f"**执行业务目录**：{business_directory}\n"
        f"**测试总数**：{total}\n"
        f"**通过数量**：{passed}\n"
        f"**失败数量**：{failed}\n"
        f"**跳过数量**：{skipped}\n"
        f"**执行耗时**：{duration:.2f} 秒\n"
        f"**执行结果**：{result}"
    )

    # 成功是否通知由 .env 中的 LARK_NOTIFY_ON_SUCCESS 控制
    # 失败始终发送通知
    if failed == 0 and not NOTIFY_ON_SUCCESS:
        logger.info("测试全部通过，但已关闭成功通知，跳过 Lark 消息")
        return

    send_lark_message(
        title=f"🧪 Pytest 巡检执行结果：{result}",
        content=content,
        is_error=is_error
    )