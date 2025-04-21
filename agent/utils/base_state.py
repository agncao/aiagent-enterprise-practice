from typing_extensions import TypedDict, Annotated
from langgraph.graph import add_messages
from langchain_core.messages import AIMessage
import logging

logger = logging.getLogger(__name__)

# 基础状态类，包含所有状态共有的字段
class BaseState(TypedDict):
    """基础状态类，包含所有状态共有的字段"""
    messages: Annotated[list, add_messages]  # 存储对话上下文
    user_input: str  # 用户输入
    action: str = None  # 动作类型，例如 "tool_call"
    tool_call_name:str = None  # 工具名称
    user_action: bool = False  # 是否需要用户手动输入
    thread_id: str = None  # 对话ID


class StateUtils:
    """
    检查状态是否准备好调用工具
    
    Args:
        state (BaseState): 当前状态
        
    Returns:
        bool: 是否准备好调用工具
    """

    @staticmethod
    def ready_call_tool(state: BaseState) -> bool:
        if "messages" in state and len(state["messages"]) > 0:
            last_message = state["messages"][-1]
            if isinstance(last_message, AIMessage) and "action" in state and state["action"] == "tool_call":
                return True
        return False