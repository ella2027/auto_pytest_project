"""
登录认证工具
负责从 login_tokens.csv 中动态获取用户 Token
"""
import csv
from pathlib import Path
from common.logger import logger

# 获取项目根目录
PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Token CSV 文件路径
TOKEN_FILE = PROJECT_ROOT / "test_data" / "csv" / "login_tokens.csv"

def load_access_token(login_name=None):
    """
    从 login_tokens.csv 中读取有效 Token

    参数：
        login_name：指定用户账号，不传则默认读取第一条成功记录

    返回：
        login_name：登录账号
        access_token：用户 Token
    """

    # 判断 CSV 文件是否存在
    if not TOKEN_FILE.is_file():
        raise FileNotFoundError(
            f"Token 文件不存在：{TOKEN_FILE}，请先执行登录用例"
        )

    # 读取 CSV 文件
    with TOKEN_FILE.open(
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as file:

        rows = list(csv.DictReader(file))

    # 判断 CSV 是否有数据
    if not rows:
        raise ValueError("login_tokens.csv 中没有用户数据")

    # 遍历 CSV 中的用户记录
    for row in rows:

        # 获取账号
        row_login = (row.get("loginName") or "").strip()

        # 获取 Token
        token = (row.get("access_token") or "").strip()

        # 获取登录状态
        status = (row.get("status") or "").strip().upper()

        # 如果指定了账号，只读取指定账号
        if login_name and row_login != login_name:
            continue

        # 只使用登录成功且 Token 不为空的记录
        if status == "SUCCESS" and token:

            # 日志只打印账号，不打印 Token
            logger.info(
                "成功获取用户 Token，账号：%s",
                row_login
            )

            return row_login, token

    raise ValueError(
        "login_tokens.csv 中没有找到有效 Token，"
        "请检查 status 和 access_token 字段"
    )