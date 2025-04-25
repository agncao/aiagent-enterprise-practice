from langchain_core.tools import tool
from pydantic import BaseModel

@tool
class UserConfirm(BaseModel):
    """
    是否需要用户确认信息
    """
    request: str

@tool
def continue_workflow_with_tool_result(state):
    """
    用于WebSocket场景：收到前端返回的工具结果后，恢复流程继续执行
    """
    # 这里假设前端返回的结果已写入 state["tool_result"]
    # 你可以根据需要处理 tool_result 并返回新的 state
    return state

agent_tools = [UserConfirm]
