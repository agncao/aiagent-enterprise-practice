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
    collected_params: list = []  # 已收集的参数，改为列表类型
    action: str = None  # 动作类型，例如 "tool_call"
    tool_name: str = None  # 工具名称
    tool_args: str = None  # 工具参数




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
            if isinstance(last_message, AIMessage) and state["action"] == "tool_call":
                return True
        return False