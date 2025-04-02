from typing_extensions import TypedDict, Annotated
from langgraph.graph import add_messages

# 基础状态类，包含所有状态共有的字段
class BaseState(TypedDict):
    """基础状态类，包含所有状态共有的字段"""
    messages: Annotated[list, add_messages]  # 存储对话上下文
    user_input: str  # 用户输入
