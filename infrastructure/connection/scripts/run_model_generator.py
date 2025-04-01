"""
运行模型生成器
"""
import sys
import os
from __init__ import PROJECT_ROOT

# 添加项目根目录到Python路径
sys.path.append(PROJECT_ROOT)

# 运行生成器
from infrastructure.connection.scripts.generate_models import *

print(f"模型生成完成，请检查 {PROJECT_ROOT}/infrastructure/connection/repository/models 目录")