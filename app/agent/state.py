from app.agent.assistant_type import AssistantType
from app.utils.base_state import BaseState

# 扩展的助理状态类
class State(BaseState):
    """通用助理状态"""
    params: dict = {}  # 存储查询参数
    result: list = None # 工具执行结果
    params_ready: bool = False  # 参数是否准备好的标志
    assistant_name: str  # 助理名称
    assistant_type: AssistantType  # 助理类型
