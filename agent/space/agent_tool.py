from langchain_core.tools import tool
from typing import Dict, Any
from infrastructure.logger import log

@tool
def confirm_user_action(action_description: str, details: Dict[str, Any]):
    """
    在执行创建或修改操作前，调用此工具向用户确认信息。

    Args:
        action_description (str): 需要确认的操作描述 (例如 "创建以下场景", "添加以下实体")。
        details (Dict[str, Any]): 需要用户确认的具体信息。

    Returns:
        Dict[str, Any]: 一个包含确认请求的消息，引导用户确认。
    """
    log.info(f"请求用户确认操作: {action_description}, 细节: {details}")
    details_str = "\n".join([f"- {k}: {v}" for k, v in details.items() if v is not None])
    prompt = f"请确认是否要{action_description}：\n{details_str}\n请输入 '是' 或 '否'。"
    # 同样，这个工具生成一个需要AI回复给用户的提示
    return {"prompt_to_user": prompt, "action": "confirm","has_answered": False}

agent_tools = [confirm_user_action]
