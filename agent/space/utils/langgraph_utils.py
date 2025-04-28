import json
from typing import Any
from infrastructure.logger import log
from agent.space.space_types import ToolInfo

def get_tool_info(last_message)->ToolInfo:
    '''
    从 SpaceState 中获取工具调用的 name, args, type, call_id 等信息

    Args:
        last_message (Message): 包含工具调用信息的消息
    Returns:
        ToolInfo: 包含工具调用信息的字典
    '''
    try:
        if last_message and last_message.additional_kwargs and last_message.additional_kwargs.get("tool_calls", []):
            #获取tool_calls
            tool_calls = last_message.additional_kwargs.get("tool_calls", [])
            if not tool_calls:
                return None
                
            tool_name = tool_calls[0]['function']['name']
            arguments_str = tool_calls[0]['function']['arguments']
            
            # 记录原始参数字符串，便于调试
            log.debug(f"Tool arguments string: {arguments_str}")
            
            try:
                tool_args = json.loads(arguments_str)
            except json.JSONDecodeError as e:
                log.error(f"JSON解析错误: {e}, 原始字符串: {arguments_str}")
                # 尝试修复可能的JSON格式问题
                if arguments_str.endswith('"') and not arguments_str.endswith('"}'):
                    fixed_args = arguments_str + '}'
                    log.debug(f"尝试修复JSON: {fixed_args}")
                    tool_args = json.loads(fixed_args)
                else:
                    # 如果无法修复，返回空字典
                    tool_args = {}
            
            tool_type = tool_calls[0]['type']
            return ToolInfo(name=tool_name, args=tool_args, type=tool_type, call_id=tool_calls[0]['id'])
    except Exception as e:
        log.error(f"获取工具信息时出错: {e}")
    
    return None