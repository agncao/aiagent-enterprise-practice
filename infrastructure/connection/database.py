"""
数据库配置模块
"""
import os
from dotenv import load_dotenv
from infrastructure.config import config

# 加载环境变量
load_dotenv()

# 数据库配置
DB_CONFIG = {
    "url": config.get("database.url"),
    "username": config.get("database.username"),
    "password": config.get("database.password"),
    "database": config.get("database.database"),
}

# 构建数据库URL
DB_URL = f"mysql+pymysql://{DB_CONFIG['username']}:{DB_CONFIG['password']}@{DB_CONFIG['url']}"