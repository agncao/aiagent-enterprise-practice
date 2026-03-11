from langgraph.constants import END
from langgraph.graph import StateGraph
from langgraph.prebuilt import tools_condition
from app.multi_agent.assistants.assistant import Assistant
from app.multi_agent.assistants.runnable.hotel_runnable import hotel_assistant_runnable,hotel_tools
from app.multi_agent.tools.base import create_tool_node_with_fallback
from app.multi_agent.workflow.base import split_tools,leave_skill
from typing import Callable, Literal
from app.multi_agent.assistants.data_model import CompleteOrEscalate
from app.multi_agent.state import CtripFlowState
from app.multi_agent.workflow.entry_node_producer import create_entry_node
from config import get_logger

logger = get_logger(__name__)

HOTEL_WRITE_TOOLS = ["book_hotel", "cancel_hotel", "update_hotel_dates"]
hotel_read_tools, hotel_write_tools = split_tools(hotel_tools, HOTEL_WRITE_TOOLS)
logger.info(f"酒店助手读取工具: {[t.name for t in hotel_read_tools]}")

def route_hotel_assistant(state: CtripFlowState) -> Literal[
    "hotel_read_tools",
    "hotel_write_tools",
    "leave_skill",
    "__end__",]:
    """
    根据当前状态路由酒店预订流程。

    :param state: 当前对话状态字典
    :return: 下一步应跳转到的节点名
    """

    route = tools_condition(state)  # 判断下一步的方向
    if route == END:
        return END  # 如果结束条件满足，则返回END
    messages = state["messages"]
    if messages and messages[-1].tool_calls:
        tool_calls = state["messages"][-1].tool_calls  # 获取最后一条消息中的工具调用
        did_cancel = any(tc["name"] == CompleteOrEscalate.__name__ for tc in tool_calls)  # 检查是否调用了CompleteOrEscalate

        if did_cancel:
            return "leave_skill"  # 如果用户请求取消或退出，则跳转至leave_skill节点
        if any(tc["name"] in HOTEL_WRITE_TOOLS for tc in tool_calls):
            return "hotel_write_tools"
        return "hotel_read_tools"
    return "__end__"
    
def create_workflow(builder: StateGraph) -> StateGraph:
    """
    创建酒店预订工作流
    """
    builder.add_node("hotel_entry", create_entry_node("酒店助手", "hotel_assistant"))
    builder.add_node("hotel_assistant", Assistant(hotel_assistant_runnable))
    builder.add_edge("hotel_entry", "hotel_assistant")

    builder.add_node("hotel_read_tools", create_tool_node_with_fallback(hotel_read_tools))
    builder.add_node("hotel_write_tools", create_tool_node_with_fallback(hotel_write_tools))
    builder.add_conditional_edges("hotel_assistant", route_hotel_assistant,
    ["hotel_read_tools", "hotel_write_tools", "leave_skill",END])
    builder.add_edge("hotel_write_tools", "hotel_assistant")
    builder.add_edge("hotel_read_tools", "hotel_assistant")
    return builder
