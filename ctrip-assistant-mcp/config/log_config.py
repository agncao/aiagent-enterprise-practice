import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Dict, Any
from . import CONFIG
# if str(PROJECT_ROOT) not in sys.path:
#     sys.path.insert(0, str(PROJECT_ROOT))
# try:
# except ImportError:
#     from config import CONFIG

PROJECT_ROOT = Path(__file__).resolve().parent.parent
# 确保日志目录存在
LOG_DIR = PROJECT_ROOT / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

def setup_logging() -> None:
    """
    根据配置文件初始化日志系统
    """
    # 获取日志配置
    log_config: Dict[str, Any] = CONFIG.get("logging", {})
    log_level = log_config.get("level", "INFO")
    log_format = log_config.get("format", "%(asctime)s - %(levelname)s - %(message)s")
    
    # 创建格式化器
    formatter = logging.Formatter(log_format)
    
    # 获取根日志器
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # 清空已有处理器（避免重复输出）
    root_logger.handlers.clear()
    
    # 配置处理器
    handlers_config = log_config.get("handlers", [])
    file_config = log_config.get("file", {})
    
    for handler_config in handlers_config:
        handler_type = handler_config.get("type")
        handler_level = handler_config.get("level", log_level)
        
        if handler_type == "console":
            # 控制台处理器
            console_handler = logging.StreamHandler()
            console_handler.setLevel(getattr(logging, handler_level.upper()))
            console_handler.setFormatter(formatter)
            root_logger.addHandler(console_handler)
        
        elif handler_type == "file":
            # 文件处理器（带轮转）
            filename = handler_config.get("filename", file_config.get("path", str(LOG_DIR / "ctrip_assistant.log")))
            if not os.path.isabs(filename):
                filename = str(PROJECT_ROOT / filename)
            Path(filename).parent.mkdir(parents=True, exist_ok=True)
            max_size = file_config.get("max_size", "10MB")
            backup_count = file_config.get("backup_count", 5)
            
            # 转换大小字符串为字节
            max_size_bytes = convert_size_to_bytes(max_size)
            
            file_handler = RotatingFileHandler(
                filename=filename,
                maxBytes=max_size_bytes,
                backupCount=backup_count,
                encoding=file_config.get("encoding", "utf-8")
            )
            file_handler.setLevel(getattr(logging, handler_level.upper()))
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)

def convert_size_to_bytes(size_str: str) -> int:
    """
    将大小字符串（如10MB、1GB）转换为字节数
    """
    size_str = size_str.strip().upper()
    if size_str.endswith("KB"):
        return int(size_str[:-2]) * 1024
    elif size_str.endswith("MB"):
        return int(size_str[:-2]) * 1024 * 1024
    elif size_str.endswith("GB"):
        return int(size_str[:-2]) * 1024 * 1024 * 1024
    else:
        # 默认按字节处理
        return int(size_str)

# 创建全局日志工具函数
def get_logger(name: str) -> logging.Logger:
    """
    获取命名日志器
    :param name: 日志器名称，通常使用 __name__
    :return: 配置好的日志器
    """
    return logging.getLogger(name)

if __name__ == "__main__":
    setup_logging()
    logger = get_logger(__name__)
    logger.info("这是一条测试日志")
