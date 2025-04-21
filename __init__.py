"""
AI Agent Enterprise Practice
===========================

这是一个企业级AI Agent实践项目，提供了灵活的配置管理和监控系统。
"""

import os
import sys
from pathlib import Path

# 定义项目根目录的绝对路径
PROJECT_ROOT = Path(__file__).parent.absolute()
print(PROJECT_ROOT)

# 将项目根目录添加到Python路径
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# 将项目根目录设置为环境变量，以便其他模块可以访问
os.environ['PROJECT_ROOT'] = str(PROJECT_ROOT)

__all__ = ['PROJECT_ROOT']