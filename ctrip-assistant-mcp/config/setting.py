import os
from pathlib import Path
import yaml
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# 获取当前环境
ENV = os.getenv("ENV", "dev")

# 加载对应环境的配置
def load_config() -> dict:
    config_path = BASE_DIR / "config" / f"{ENV}.yml"
    if not config_path.exists():
        raise FileNotFoundError(f"配置文件 {config_path} 不存在")
    
    with config_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)