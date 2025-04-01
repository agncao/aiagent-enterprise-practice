"""
自动生成数据库模型脚本
"""
import os
from pathlib import Path
from __init__ import PROJECT_ROOT
from infrastructure.config import config
import pymysql
from sqlalchemy import create_engine, inspect
from sqlalchemy.ext.declarative import declarative_base
from jinja2 import Template
from infrastructure.connection.database import DB_URL

# 创建输出目录
MODELS_DIR = f"{PROJECT_ROOT}/infrastructure/connection/repository/models"
os.makedirs(MODELS_DIR, exist_ok=True)

# 创建SQLAlchemy引擎
engine = create_engine(DB_URL)
inspector = inspect(engine)

# 模型模板
MODEL_TEMPLATE = """\"\"\"
{{ table_name }} 数据模型
自动生成于 models
\"\"\"
from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Text, ForeignKey, DECIMAL
from sqlalchemy.orm import relationship
from infrastructure.connection.base import Base

class {{ class_name }}(Base):
    \"\"\"{{ table_comment }}\"\"\"
    __tablename__ = '{{ table_name }}'

{% for column in columns %}
    {{ column.name }} = Column({{ column.type }}, {% if column.primary_key %}primary_key=True, {% endif %}{% if column.autoincrement %}autoincrement=True, {% endif %}{% if column.nullable == False %}nullable=False, {% endif %}{% if column.default %}default={{ column.default }}, {% endif %}{% if column.comment %}comment='{{ column.comment }}'{% endif %})
{% endfor %}
"""

# 获取所有表名
table_names = inspector.get_table_names()

# 创建基础模型文件
base_file_path = os.path.join(PROJECT_ROOT, "infrastructure/connection/repository/models/base.py")
if not os.path.exists(base_file_path):
    with open(base_file_path, "w") as f:
        f.write("""\"\"\"
数据库基础模型定义
\"\"\"
from sqlalchemy.ext.declarative import declarative_base

# 创建基础模型类
Base = declarative_base()
""")
    print(f"创建基础模型文件: {base_file_path}")

# 创建__init__.py文件
init_file_path = os.path.join(MODELS_DIR, "__init__.py")
if not os.path.exists(init_file_path):
    with open(init_file_path, "w") as f:
        f.write('"""模型包"""')
    print(f"创建模型包初始化文件: {init_file_path}")

# 为每个表生成模型
for table_name in table_names:
    # 获取表注释
    try:
        conn = pymysql.connect(
            host="localhost",
            port=3306,
            user="root",
            password="root",
            database="information_schema"
        )
        cursor = conn.cursor()
        cursor.execute(f"SELECT TABLE_COMMENT FROM TABLES WHERE TABLE_SCHEMA = 'ctrip_ai' AND TABLE_NAME = '{table_name}'")
        result = cursor.fetchone()
        table_comment = result[0] if result and result[0] else f"{table_name}表"
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"获取表注释失败: {e}")
        table_comment = f"{table_name}表"
    
    # 获取列信息
    columns = []
    for column in inspector.get_columns(table_name):
        # 处理列类型
        col_type = str(column['type'])
        if 'INT' in col_type.upper():
            col_type = 'Integer'
        elif 'VARCHAR' in col_type.upper() or 'CHAR' in col_type.upper():
            col_type = f'String({column["type"].length})'
        elif 'TEXT' in col_type.upper():
            col_type = 'Text'
        elif 'DATETIME' in col_type.upper() or 'TIMESTAMP' in col_type.upper():
            col_type = 'DateTime'
        elif 'DATE' in col_type.upper():
            col_type = 'Date'
        elif 'DECIMAL' in col_type.upper() or 'NUMERIC' in col_type.upper():
            col_type = f'DECIMAL(precision={column["type"].precision}, scale={column["type"].scale})'
        elif 'FLOAT' in col_type.upper() or 'DOUBLE' in col_type.upper():
            col_type = 'Float'
        elif 'BOOLEAN' in col_type.upper() or 'TINYINT(1)' in col_type.upper():
            col_type = 'Boolean'
        else:
            col_type = 'String(255)'  # 默认类型
        
        # 获取列注释
        try:
            conn = pymysql.connect(
                host="localhost",
                port=3306,
                user="root",
                password="root",
                database="information_schema"
            )
            cursor = conn.cursor()
            cursor.execute(f"SELECT COLUMN_COMMENT FROM COLUMNS WHERE TABLE_SCHEMA = 'ctrip_ai' AND TABLE_NAME = '{table_name}' AND COLUMN_NAME = '{column['name']}'")
            result = cursor.fetchone()
            column_comment = result[0] if result and result[0] else ""
            cursor.close()
            conn.close()
        except Exception as e:
            print(f"获取列注释失败: {e}")
            column_comment = ""
        
        columns.append({
            'name': column['name'],
            'type': col_type,
            'primary_key': column.get('primary_key', False),
            'autoincrement': 'autoincrement' in column and column['autoincrement'],
            'nullable': column.get('nullable', True),
            'default': repr(column.get('default')) if column.get('default') is not None else None,
            'comment': column_comment
        })
    
    # 生成类名 (表名转为驼峰命名)
    class_name = ''.join(word.title() for word in table_name.split('_'))
    
    # 渲染模板
    template = Template(MODEL_TEMPLATE)
    model_content = template.render(
        table_name=table_name,
        class_name=class_name,
        table_comment=table_comment,
        columns=columns
    )
    
    # 写入文件
    model_file_path = os.path.join(MODELS_DIR, f"{table_name}.py")
    with open(model_file_path, "w") as f:
        f.write(model_content)
    
    print(f"生成模型文件: {model_file_path}")

print("所有模型生成完成！")