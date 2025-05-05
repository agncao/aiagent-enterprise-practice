import ast
import json
from typing import Any
from infrastructure.logger import log


def get_tool_info(last_message)->dict:
    '''
    从 SpaceState 中获取工具 name, args, type, call_id 等信息

    Args:
        last_message (Message): 包含工具信息的消息
    Returns: 获取工具信息
    '''
    try:
        if last_message and last_message.additional_kwargs and last_message.additional_kwargs.get("tool_calls", []):
            #获取tool_calls
            tool_calls = last_message.additional_kwargs.get("tool_calls", [])
            if not tool_calls:
                return None
                
            tool_name = tool_calls[0]['function']['name']
            arguments_str = tool_calls[0]['function']['arguments']
            log.debug(f"Tool arguments string: {arguments_str}")
            
            # 解析参数字符串
            if is_json_format(arguments_str):
                tool_args = json.loads(arguments_str)
            else:
                log.debug("使用 ast.literal_eval 解析 Python 字典字面量")
                tool_args = ast.literal_eval(arguments_str)
            
            tool_type = tool_calls[0]['type']
            
            return {"name": tool_name,"args": tool_args, "type": tool_type,"call_id": tool_calls[0]['id']}
    except Exception as e:
        log.error(f"获取工具信息时出错: {e}")
    
    return None


def is_json_format(s: str) -> bool:
    """判断字符串是否符合 JSON 格式（键使用双引号）"""
    # JSON 格式的对象或数组必须以 { 或 [ 开头，以 } 或 ] 结尾
    s = s.strip()
    if not (s.startswith('{') and s.endswith('}')) and not (s.startswith('[') and s.endswith(']')):
        return False
    
    # JSON 中的键必须使用双引号，检查第一个键是否使用双引号
    if s.startswith('{'):
        # 跳过 { 后查找第一个非空白字符，应该是 "
        for i in range(1, len(s)):
            if s[i].strip():
                return s[i] == '"'
    
    return True

def valid_tool_call(last_message):
    errors = []  # 初始化 errors 列表
    
    if last_message and last_message.additional_kwargs and last_message.additional_kwargs.get("tool_calls", []):
        tool_calls = last_message.additional_kwargs.get("tool_calls", [])
        if not tool_calls:
            return

        # 检测无效工具调用
        if hasattr(last_message, 'invalid_tool_calls') and last_message.invalid_tool_calls:
            for invalid_call in last_message.invalid_tool_calls:  # 使用 last_message 而非 response
                error_info = {
                    "tool": invalid_call.get("name"),
                    "args": invalid_call.get("args"),
                    "error": invalid_call.get("error") or "参数验证失败"
                }
                errors.append(f"工具 {error_info['tool']} 调用失败: {error_info['error']}")
        
    # 统一处理错误
    if errors:
        error_msg = "工具调用参数错误:\n" + "\n".join(errors)
        raise ValueError(error_msg) 
