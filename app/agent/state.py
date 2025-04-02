from typing_extensions import TypedDict, Annotated
from langchain_core.messages import HumanMessage, AIMessage
from app.agent.assistant_type import AssistantType
from langgraph.graph import add_messages, StateGraph, END

# 基础状态类，包含所有状态共有的字段
class BaseState(TypedDict):
    """基础状态类，包含所有状态共有的字段"""
    messages: Annotated[list, add_messages]  # 存储对话上下文
    user_input: str  # 用户输入

# 扩展的助理状态类
class State(BaseState):
    """通用助理状态"""
    params: dict  # 存储查询参数
    result: list  # 工具执行结果
    params_ready: bool  # 参数是否准备好的标志
    assistant_name: str  # 助理名称
    assistant_type: AssistantType  # 助理类型
