from langchain_core.tools import tool
from typing import Dict, Any
from langchain_core.messages import AIMessage
from infrastructure.logger import log
from agent.space.space_types import Operation,SpaceState
from agent.space.space_write_tool import write_tools

# @tool
# def confirm_user_action(action_description: str, details: Dict[str, Any]):
#     """
#     在执行创建或修改操作前，调用此工具向用户确认信息。

#     Args:
#         action_description (str): 需要确认的操作描述 (例如 "创建以下场景", "添加以下实体")。
#         details (Dict[str, Any]): 需要用户确认的具体信息。

#     Returns:
#         Dict[str, Any]: 一个包含确认请求的消息，引导用户确认。
#     """
#     log.info(f"请求用户确认操作: {action_description}, 细节: {details}")
#     details_str = "\n".join([f"- {k}: {v}" for k, v in details.items() if v is not None])
#     prompt = f"请确认是否要{action_description}：\n{details_str}\n请输入 '是' 或 '否'。"
#     # 同样，这个工具生成一个需要AI回复给用户的提示
#     return {"prompt_to_user": prompt, "action": "confirm","has_answered": False}


def format_tool_call_response(state: SpaceState):
    """
    优雅的格式化外部平台执行工具发出的指令后所返回来的结果
    
    """
    log.info(f"format_tool_call_response: {state}")
    res = state.get("tool_call_response",None)
    if res:
        content = f"{res['message'],参数为:res['args']}"
        if res["func"] in [tool.__name__ for tool in write_tools] and res["data"] is not None:
            data_lines = "\n".join([f"- {d}" for d in res["data"]])
            content += f"，返回结果是：\n{data_lines}"
        elif res["func"] in [tool.__name__ for tool in write_tools]:
            content += "，无返回结果"
        return AIMessage(content=content)
    return AIMessage(content="无响应")

agent_tools = [format_tool_call_response]
