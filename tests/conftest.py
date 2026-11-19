"""创建和管理接口请求"""
import pytest
from common.auth import load_access_token
from configs.settings import DEFAULT_HEADERS
import time
from common.lark_inspector import send_pytest_summary
from pathlib import Path

@pytest.fixture #表示不是一个普通函数，而是一个测试用例资源提供函数，通过参数自动注入到测试函数中
def api_client():
    """创建管理接口请求的客户端"""
    from common.http_client import ApiClient
    # 获取登录账户和访问令牌
    login_name, access_token = load_access_token()
    headers = DEFAULT_HEADERS.copy()
    headers["Authorization"] = access_token
    client = ApiClient(headers=headers)
    print(f"\n当前使用账户：{login_name}")
    yield client
    client.close()


# 记录测试开始时间
_SESSION_START_TIME = time.time()


def pytest_sessionfinish(session, exitstatus):
    """
    Pytest 测试结束钩子。

    无论执行单个文件还是批量执行目录，
    整个 Pytest Session 结束时只发送一次汇总通知。
    """

    # 获取 pytest 终端统计信息
    terminal_reporter = session.config.pluginmanager.get_plugin(
        "terminalreporter"
    )

    if terminal_reporter is None:
        print("未获取到 Pytest 统计信息，跳过 Lark 通知")
        return

    stats = terminal_reporter.stats

    # 使用 get()，避免某种结果不存在时触发 KeyError
    passed = len(stats.get("passed", []))
    failed = (
        len(stats.get("failed", []))
        + len(stats.get("error", []))
    )
    skipped = len(stats.get("skipped", []))

    duration = time.time() - _SESSION_START_TIME

    print("\n========== 准备发送 Lark 通知 ==========")
    print(f"测试总数：{passed + failed + skipped}")
    print(f"通过数量：{passed}")
    print(f"失败数量：{failed}")
    print(f"跳过数量：{skipped}")
    # 自动识别本次执行的业务目录
    business_dirs = set()

    tests_root = Path(session.config.rootpath) / "tests"

    for item in session.items:
        try:
            relative_path = Path(str(item.path)).relative_to(tests_root)
            if relative_path.parts:
                business_dirs.add(relative_path.parts[0])
        except ValueError:
            continue

    if len(business_dirs) == 1:
        business_directory = next(iter(business_dirs))
    elif len(business_dirs) > 1:
        business_directory = "、".join(sorted(business_dirs))
    else:
        business_directory = "未识别"
    try:
        send_pytest_summary(
            passed=passed,
            failed=failed,
            skipped=skipped,
            duration=duration,
            business_directory=business_directory
        )
        print("========== Lark 通知发送流程已执行 ==========")

    except Exception as e:
        print(f"========== Lark 通知发送异常：{e} ==========")
    """
    整个 Pytest 执行结束后触发。

    单文件执行：发送一次通知
    目录批量执行：发送一次汇总通知
    全项目执行：发送一次汇总通知
    """

    print("\n========== Pytest 测试执行结束 ==========")

    results = list(_TEST_RESULTS.values())

    total = len(results)

    passed = sum(
        1 for item in results
        if item["outcome"] == "passed"
    )

    failed = sum(
        1 for item in results
        if item["outcome"] == "failed"
    )

    skipped = sum(
        1 for item in results
        if item["outcome"] == "skipped"
    )

    duration = sum(
        item["duration"] for item in results
    )

    # 收集失败用例
    failures = [
        {
            "name": item["name"],
            "reason": item["reason"],
        }
        for item in results
        if item["outcome"] == "failed"
    ]

    # 获取本次执行范围
    scope = " ".join(str(arg) for arg in session.config.args)

    summary = {
        "scope": scope or "Pytest 自动化测试",
        "total": total,
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
        "duration": duration,
        "failures": failures,
    }

    print(f"测试总数：{total}")
    print(f"通过数量：{passed}")
    print(f"失败数量：{failed}")
    print(f"跳过数量：{skipped}")

    print("========== 准备发送飞书通知 ==========")

    try:
        send_pytest_summary(summary)
        print("========== 飞书通知调用完成 ==========")

    except Exception as e:
        print(f"========== 飞书通知发送异常：{e} ==========")

    """
    当前 Pytest 会话结束后统一发送一次通知。
    """
    if not _TEST_RESULTS:
        return

    passed = 0
    failed = 0
    skipped = 0
    duration = 0
    failures = []

    for nodeid, result in _TEST_RESULTS.items():

        duration += result["duration"]

        if result["failed"]:
            failed += 1
            failures.append(
                f"{nodeid}\n{result['failure'][:500]}"
            )

        elif result["skipped"]:
            skipped += 1

        elif result["passed"]:
            passed += 1

    target_name = get_target_name(session)

    try:
        send_pytest_summary(
            target_name=target_name,
            passed=passed,
            failed=failed,
            skipped=skipped,
            duration=duration,
            failures=failures
        )

    except Exception as e:
        print(f"Lark 通知异常：{e}")