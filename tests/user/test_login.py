import csv
from pathlib import Path
import pytest
from configs.settings import BASE_URL, DEFAULT_HEADERS
from common.http_client import ApiClient
PROJECT_ROOT = Path(__file__).resolve().parents[2]  # 项目根目录

USERS_FILE = PROJECT_ROOT  / "test_data" / "csv" / "login_users.csv"
OUTPUT_FILE = PROJECT_ROOT / "test_data" / "csv" / "login_tokens.csv"

LOGIN_PATH = "/user/api/user/login"


def read_users():
    """读取待登录的用户列表"""
    with open(USERS_FILE, "r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def save_tokens(rows):
    """将成功获取的 Token 保存到 CSV"""
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_FILE, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["loginName", "access_token", "status", "message"],
        )
        writer.writeheader()
        writer.writerows(rows)


def test_batch_login():
    users = read_users()
    assert users, "login_users.csv 中没有用户数据"

    # 登录接口不需要 Authorization，因此创建不带该请求头的客户端。
    login_headers = {
        key: value
        for key, value in DEFAULT_HEADERS.items()
        if key.lower() != "authorization"
    }
    client = ApiClient(headers=login_headers)

    results = []

    for user in users:
        login_name = user["loginName"].strip()
        password = user["loginPassword"]

        # 每个用户单独构造请求体，避免多个用户共用同一账号。
        body = {
            "device": "iPad Pro 12-Inch 3",
            "fingerprint": "8482eaad7cda0ac6b761f61ca4368c02",
            "googleCode": "",
            "loginName": login_name,
            "loginPassword": password,
            "signType": 3,
        }

        try:
            response = client.post(
                LOGIN_PATH,
                json=body,
                timeout=(3, 15),
            )
            response.raise_for_status()
            data = response.json()

            access_token = (
                data.get("data", {}).get("access_token")
            )

            if data.get("code") == 200 and access_token:
                results.append({
                    "loginName": login_name,
                    "access_token": access_token,
                    "status": "SUCCESS",
                    "message": "登录成功",
                })
            else:
                results.append({
                    "loginName": login_name,
                    "access_token": "",
                    "status": "FAILED",
                    "message": str(data.get("msg", "未获取到 access_token")),
                })

        except Exception as exc:
            results.append({
                "loginName": login_name,
                "access_token": "",
                "status": "FAILED",
                "message": type(exc).__name__,
            })

    save_tokens(results)

    success_count = sum(
        row["status"] == "SUCCESS" for row in results
    )

    print(f"总用户数：{len(users)}")
    print(f"登录成功：{success_count}")
    print(f"登录失败：{len(users) - success_count}")
    print(f"Token 文件：{OUTPUT_FILE}")

    assert success_count == len(users), (
        f"有 {len(users) - success_count} 个用户登录失败，"
        "请检查 login_tokens.csv"
    )