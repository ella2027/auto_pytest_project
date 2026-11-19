# AstroX API 自动化测试项目

基于 **Python + Pytest + Requests + YAML + CSV** 搭建的 API 自动化测试项目，主要用于 AstroX 交易业务接口测试。

项目目前包含以下能力：

- 通过 `configs/settings.py` 统一管理测试环境、Base URL 和公共请求头。
- 通过 `tests/user/test_login.py` 批量读取测试账号并执行登录。
- 登录成功后，将每个账号的 `access_token` 写入 `test_data/csv/login_tokens.csv`。
- 业务测试用例运行时，通过 `tests/conftest.py` 自动读取有效 Token，并注入 `Authorization` 请求头。
- 通过 `common/http_client.py` 统一封装 GET、POST、PUT、DELETE 请求。
- 通过 YAML 管理接口的请求方法和路径；请求参数可以直接写在测试用例中。
- 通过统一日志模块记录运行日志。
- 提供飞书/Lark Webhook 通知工具，可供巡检脚本调用。

> **重要：** 下单接口会产生真实委托或影响测试账户资产。请确认当前 `ENV`、Base URL、账号和请求参数均指向允许测试的环境后，再执行下单用例。不要在未确认的情况下使用生产环境。

---

## 1. 项目目录结构

```text
auto_pytest_project/
│
├── common/                         # 公共工具层
│   ├── __init__.py
│   ├── auth.py                      # 从 login_tokens.csv 读取有效 Token
│   ├── data_loader.py               # YAML 文件读取工具
│   ├── http_client.py               # Requests HTTP 客户端封装
│   ├── lark_inspector.py            # 飞书/Lark 消息及巡检通知工具
│   └── logger.py                    # 统一日志配置
│
├── configs/                         # 项目配置层
│   ├── __init__.py
│   └── settings.py                  # 环境、Base URL、公共 Headers 配置
│
├── logs/                            # 运行日志目录（运行后生成）
│   └── test.log
│
├── test_data/                       # 测试数据
│   ├── csv/
│   │   ├── login_users.csv          # 登录账号及密码（本地维护，不提交 Git）
│   │   └── login_tokens.csv         # 登录成功后生成的 Token（不提交 Git）
│   │
│   └── yaml/
│       └── order_request.yaml       # 订单接口的 method、path 配置
│
├── tests/                           # 测试用例层
│   ├── __init__.py
│   ├── conftest.py                  # Pytest Fixture：创建客户端并注入 Token
│   │
│   ├── user/
│   │   └── test_login.py            # 批量登录并生成 Token CSV
│   │
│   └── order/
│       ├── test_select.py           # 订单查询用例（按实际实现补充）
│       └── test_valueSubmit.py      # 现货/币币下单接口用例
│
├── .env                             # 本地环境变量及密钥（自行创建，不提交 Git）
├── .env.example                     # 环境变量配置模板
├── .gitignore                       # Git 忽略规则
├── pytest.ini                       # Pytest 配置
├── requirements.txt                 # Python 依赖
└── README.md                        # 项目说明文档
```

---

## 2. 环境准备

### 2.1 Python 环境

建议使用 Python 3.9 或更高版本。

在项目根目录执行：

```bash
python3 --version
```

### 2.2 创建虚拟环境

macOS / zsh：

```bash
# 进入项目根目录
cd auto_pytest_project

# 创建虚拟环境
python3 -m venv .venv

# 激活虚拟环境
source .venv/bin/activate
```

激活成功后，终端前面通常会显示：

```text
(.venv)
```

### 2.3 安装依赖

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

当前依赖主要包括：

| 依赖 | 用途 |
|---|---|
| pytest | 测试用例组织、执行和断言 |
| requests | 发送 HTTP 请求 |
| python-dotenv | 读取 `.env` 环境变量 |
| pyyaml | 读取 YAML 测试配置 |
| allure-pytest | 生成 Allure 测试结果数据 |
| playwright | 浏览器自动化扩展依赖；当前 API 用例不依赖它 |

---

## 3. 环境配置

### 3.1 创建 `.env`

复制模板：

```bash
cp .env.example .env
```

打开项目根目录下的 `.env`，根据实际测试环境填写配置。

示例：

```dotenv
# 当前运行环境：test / staging / prod
ENV=test

# 测试环境
TEST_BASE_URL=https://你的测试环境网关域名
TEST_AUTH_TOKEN=

# 预发环境
STAGING_BASE_URL=
STAGING_AUTH_TOKEN=

# 生产环境（非必要不要配置或使用）
PROD_BASE_URL=
PROD_AUTH_TOKEN=

# 飞书机器人
LARK_WEBHOOK_URL=
LARK_NOTIFY_ON_SUCCESS=false
```

`settings.py` 会根据 `ENV` 选择对应的 Base URL：

| ENV 值 | 读取的 Base URL |
|---|---|
| `test` | `TEST_BASE_URL` |
| `staging` | `STAGING_BASE_URL` |
| `prod` | `PROD_BASE_URL` |

例如：

```dotenv
ENV=test
TEST_BASE_URL=https://cloud-gateway.astroxtest.com
```

运行时就会使用测试环境域名。

> `settings.py` 中的 `DEFAULT_HEADERS` 保存设备、语言、应用版本等公共请求头。当前业务用例的 `Authorization` 会由 `conftest.py` 使用 CSV 中的登录 Token 覆盖，因此业务用例通常不需要手动传 Authorization。

---

## 4. 测试账号与 Token 管理

### 4.1 准备登录账号

在以下文件中维护测试账号：

```text
test_data/csv/login_users.csv
```

文件格式：

```csv
loginName,loginPassword
test_user_01,请填写测试密码
test_user_02,请填写测试密码
```

请使用有权限且允许自动化测试的测试账号。不要把真实密码提交到 Git 仓库。

### 4.2 执行批量登录

在项目根目录执行：

```bash
pytest tests/user/test_login.py -s -v
```

登录用例会：

1. 读取 `login_users.csv` 中的账号和密码。
2. 调用登录接口 `POST /user/api/user/login`。
3. 解析响应中的 `data.access_token`。
4. 将每个账号的登录结果写入 `login_tokens.csv`。

生成文件：

```text
test_data/csv/login_tokens.csv
```

字段格式：

```csv
loginName,access_token,status,message
test_user_01,登录成功后返回的Token,SUCCESS,登录成功
test_user_02,,FAILED,失败原因
```

只有 `status=SUCCESS` 且 `access_token` 不为空的记录，才会被后续业务测试使用。

### 4.3 Token 动态注入全链路

业务测试用例只需要声明 `api_client`：

```python
def test_example(api_client):
    ...
```

运行链路如下：

```text
执行业务测试用例
        |
        v
Pytest 查找并执行 tests/conftest.py 中的 api_client Fixture
        |
        v
调用 common/auth.py 的 load_access_token()
        |
        v
重新读取 test_data/csv/login_tokens.csv
        |
        v
选择第一条 status=SUCCESS 且 access_token 非空的记录
        |
        v
复制 configs/settings.py 中的 DEFAULT_HEADERS
        |
        v
将 CSV 中的 access_token 写入 headers["Authorization"]
        |
        v
创建 ApiClient(headers=headers)
        |
        v
测试用例通过 api_client 发送请求
        |
        v
用例结束，Fixture 关闭 HTTP Session
```

相关文件职责：

| 文件 | 职责 |
|---|---|
| `common/auth.py` | 从 CSV 读取有效账号及 Token |
| `configs/settings.py` | 提供环境配置和公共 Headers |
| `tests/conftest.py` | 将 Token 注入本次测试使用的 API Client |
| `common/http_client.py` | 合并 Headers 并发送 HTTP 请求 |

**当前 Token 选择规则：** 每次业务用例初始化 `api_client` 时，都会重新读取 CSV，并默认选择第一条有效记录。当前不是多账号轮询，也不是随机选择账号。如果要指定账号，可以在后续将 Fixture 扩展为参数化方式。

登录用例本身不使用 `api_client` Fixture，因为登录前可能还没有 Token；它会创建一个不带 `Authorization` 的客户端，避免登录依赖自身生成的 Token。

---

## 5. YAML 接口配置

当前 YAML 只保存接口请求方法和路径，不重复维护公共 Headers，也不强制把请求参数放入 YAML。

文件位置：

```text
test_data/yaml/order_request.yaml
```

示例：

```yaml
# 下单接口
order_submit:
  method: POST
  path: /user/api/currency/order/submit

# 订单查询接口
order_select:
  method: GET
  path: /user/api/currency/order/select
```

通过 `common/data_loader.py` 读取：

```python
from common.data_loader import load_yaml

config = load_yaml("order_request.yaml")

method = config["order_submit"]["method"]
path = config["order_submit"]["path"]
```

`load_yaml()` 的相对路径以 `test_data/yaml/` 为基准，不需要在用例中拼接项目绝对路径。

---

## 6. 编写和执行业务测试用例

### 6.1 下单接口示例

文件：

```text
tests/order/test_valueSubmit.py
```

当前下单接口信息：

| 项目 | 内容 |
|---|---|
| 请求方式 | POST |
| 接口路径 | `/user/api/currency/order/submit` |
| 完整 URL | 当前环境的 `BASE_URL` + 接口路径 |
| Token | 由 `api_client` Fixture 动态注入 |
| 请求参数 | 在测试用例中定义 |

运行：

```bash
pytest tests/order/test_valueSubmit.py -s -v
```

当前示例请求参数：

```python
payload = {
    "symbol": "avax",
    "coin": "usdt",
    "delegateType": "0",
    "priceType": 1,
    "timeInForce": "GTC",
    "triggerPrice": "",
    "type": "0",
    "directionPriceType": 1,
    "delegatePrice": "11.000",
    "delegateTotal": "",
    "delegateValue": "1000.0000",
}
```

发送请求：

```python
response = api_client.post(
    path,
    json=payload,
    timeout=(3, 20),
)
```

无需在测试用例中再次设置公共 Headers 或 Authorization。

### 6.2 执行全部用例

```bash
pytest
```

### 6.3 常用执行命令

```bash
# 执行登录用例
pytest tests/user/test_login.py -s -v

# 执行下单用例
pytest tests/order/test_valueSubmit.py -s -v

# 执行订单目录下的用例
pytest tests/order/ -s -v

# 只执行冒烟用例
pytest -m smoke -s -v

# 只执行回归用例
pytest -m regression -s -v

# 指定测试环境执行
ENV=staging pytest tests/order/test_valueSubmit.py -s -v
```

---

## 7. 日志管理

统一日志工具位于：

```text
common/logger.py
```

日志同时输出到：

- 终端控制台
- 项目根目录的 `logs/test.log`

日志包含时间、级别、模块、代码行号和消息内容。

在代码中使用：

```python
from common.logger import logger

logger.info("测试开始")
logger.warning("当前配置缺少可选参数")
logger.error("接口请求失败")
```

日志文件按天轮转，最多保留 14 天。

不要在日志中输出密码、完整 Token、Authorization 或其他敏感信息。

---

## 8. 飞书 / Lark 通知

飞书通知工具位于：

```text
common/lark_inspector.py
```

在 `.env` 中配置：

```dotenv
LARK_WEBHOOK_URL=你的飞书机器人Webhook地址
LARK_NOTIFY_ON_SUCCESS=false
```

调用示例：

```python
from common.lark_inspector import run_inspection

def check_order_query():
    # 在这里编写请求和断言
    # 断言成功后返回用于通知展示的信息
    return {
        "接口": "订单查询",
        "结果": "正常",
    }

run_inspection("订单查询", check_order_query)
```

通知规则：

- 检查成功：`LARK_NOTIFY_ON_SUCCESS=true` 时发送绿色成功卡片。
- 断言失败或执行异常：发送红色告警卡片。
- 未配置 `LARK_WEBHOOK_URL`：跳过飞书通知，并记录 warning。

**当前项目状态说明：** `lark_inspector.py` 提供的是可调用的巡检通知工具；当前 `tests/conftest.py` 没有自动汇总所有 Pytest 用例并发送整批执行报告。若需要“每次 pytest 结束后自动把通过/失败/跳过数量发送到飞书”，需要再增加 Pytest 会话结束钩子。

---

## 9. Allure 测试报告

`pytest.ini` 已配置：

```ini
addopts = -v --alluredir=reports/allure-results --strict-markers
```

执行用例后会生成 Allure 原始结果数据。

如果本机已安装 Allure Commandline，可执行：

```bash
allure serve reports/allure-results
```

也可以先生成静态报告：

```bash
allure generate reports/allure-results -o reports/allure-report --clean
```

然后使用浏览器打开生成报告目录中的 `index.html`。

---

## 10. 新增接口用例的推荐步骤

1. 在 `test_data/yaml/` 对应 YAML 文件中增加接口的 `method` 和 `path`。
2. 在 `tests/` 对应业务目录中新建 `test_*.py` 文件。
3. 测试函数参数中声明 `api_client`，让 Fixture 自动处理 Token。
4. 使用 `load_yaml()` 读取接口方法和路径。
5. 在测试用例中组织请求参数。
6. 使用 `api_client.get()`、`post()`、`put()` 或 `delete()` 发送请求。
7. 根据接口实际响应结构编写断言。
8. 使用 `pytest 文件路径 -s -v` 执行并查看结果。

---

## 11. 常见问题排查

### 11.1 `ModuleNotFoundError` 或 `ImportError`

检查：

- 是否在项目根目录执行 pytest。
- 导入的函数名是否与源文件中定义的名称完全一致。
- 项目目录是否包含必要的 `__init__.py` 文件。

例如，当前 YAML 读取函数名称是 `load_yaml`：

```python
from common.data_loader import load_yaml
```

不要误写成 `load_yam`。

### 11.2 找不到 YAML 文件

确认文件位于：

```text
test_data/yaml/order_request.yaml
```

调用时使用相对于 YAML 目录的路径：

```python
load_yaml("order_request.yaml")
```

### 11.3 找不到 Token

确认已经先执行登录用例，并检查：

```text
test_data/csv/login_tokens.csv
```

至少存在一条：

- `status` 为 `SUCCESS`
- `access_token` 不为空

同时检查 CSV 表头是否为 `loginName,access_token,status,message`。

### 11.4 请求返回 401 / 403

检查：

- Token 是否过期。
- 登录账号是否有对应业务权限。
- 当前 `ENV` 和 `BASE_URL` 是否匹配。
- `Authorization` 是否需要 `Bearer ` 前缀。应以实际接口认证约定为准，不要自行添加或删除前缀。

### 11.5 请求地址或环境不正确

检查 `.env` 中的 `ENV` 和对应的 `<ENV>_BASE_URL` 是否正确。切换环境后，确认目标环境允许执行当前测试操作。

---

## 12. 安全与 Git 提交规范

以下文件包含账号、密码、Token 或环境密钥，不应提交到 Git：

```text
.env
test_data/csv/login_users.csv :
loginName,loginPassword
ella11@grr.la,admin123Aa@
test_data/csv/login_tokens.csv
```

项目已在 `.gitignore` 中配置忽略这些文件。

提交代码前检查：

```bash
git status
```

只提交代码、模板和不含敏感信息的文档。不要把真实密码、Token、Webhook 地址或生产环境密钥写进 README、测试代码或日志。

---

## 13. 当前项目执行顺序

首次运行或 Token 过期后，建议按以下顺序执行：

```text
准备 .env 和测试账号
        |
        v
执行批量登录
pytest tests/user/test_login.py -s -v
        |
        v
生成 / 更新 login_tokens.csv
        |
        v
执行订单或其他业务测试
pytest tests/order/test_valueSubmit.py -s -v
        |
        v
查看终端、logs/test.log 和 Allure 结果
```

后续新增业务用例时，复用 `api_client` Fixture 即可，不需要在每个测试文件中重复实现 Token 读取和公共 Headers 配置。
备注内容
# ========== 环境切换 ==========
# 可选值: test / staging / prod
# 决定下面读取哪一组 BASE_URL / AUTH_TOKEN
ENV=test

# ========== 测试环境 ==========
TEST_BASE_URL=
TEST_AUTH_TOKEN=

# ========== 预发/Staging 环境（如果有的话）==========
STAGING_BASE_URL=
STAGING_AUTH_TOKEN=

# ========== 生产环境（谨慎配置，写类接口的用例不建议在生产环境自动跑）==========
PROD_BASE_URL=
PROD_AUTH_TOKEN=

# ========== 飞书巡检通知 ==========
LARK_WEBHOOK_URL=
LARK_NOTIFY_ON_SUCCESS=true


