import os
from venv import logger
from .setting import load_config

# 全局配置对象
CONFIG = load_config()

from .log_config import setup_logging, get_logger
setup_logging()
logger=get_logger("ctrip-assistant-mcp")
logger.info("配置加载完成, 当前环境: %s", os.getenv("ENV", "dev"))