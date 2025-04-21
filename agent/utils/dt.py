import re
from datetime import datetime

def validate_datetime_regex(input_str):
    # 匹配两种格式的正则表达式
    patterns = [
        r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$",
        r"^\d{4}-\d{2}-\d{2}$"
    ]
    for pattern in patterns:
        if re.match(pattern, input_str):
            try:
                datetime.strptime(input_str, "%Y-%m-%d %H:%M:%S" if " " in input_str else "%Y-%m-%d")
                return True
            except ValueError:
                return False
    return False