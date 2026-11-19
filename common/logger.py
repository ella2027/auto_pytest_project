"""
logger.py —— 项目统一日志工具（放在 common/ 目录下）

替代到处写 print()，好处：
- 自动带时间戳、日志级别、文件名+行号，出问题时定位更快
- 同时输出到控制台和日志文件，文件按天切割，保存在 logs/ 目录，保留最近14天
- 以后想调整日志格式/级别，只需要改这一个地方，所有用例自动生效

用法：
    from common.logger import logger

    logger.debug("请求详情: %s", body)     # 调试细节，正常运行时不太需要看
    logger.info("巡检通过")                # 常规信息
    logger.warning("未配置 xxx，已跳过")    # 需要注意但不影响运行
    logger.error("接口异常: %s", e)        # 出错了
"""

import logging
from pathlib import Path
from logging.handlers import TimedRotatingFileHandler

BASE_DIR = Path(__file__).resolve().parent.parent
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

logger = logging.getLogger("astrox_auto_test")
logger.setLevel(logging.DEBUG)

_formatter = logging.Formatter(
    fmt="%(asctime)s | %(levelname)-7s | %(module)s:%(lineno)d | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# 防止 pytest 多次 import 这个模块时重复添加 handler，导致日志打印好几遍
if not logger.handlers:
    # 控制台输出
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(_formatter)
    logger.addHandler(console_handler)

    # 文件输出：每天午夜切一个新文件，最多保留14天，避免日志无限增长占满磁盘
    file_handler = TimedRotatingFileHandler(
        LOG_DIR / "test.log", when="midnight", backupCount=14, encoding="utf-8"
    )
    file_handler.setFormatter(_formatter)
    logger.addHandler(file_handler)
