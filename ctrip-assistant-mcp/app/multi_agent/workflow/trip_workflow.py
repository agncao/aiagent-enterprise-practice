from langgraph.constants import END
from langgraph.graph import StateGraph
from langgraph.prebuilt import tools_condition
from app.multi_agent.assistants.assistant import Assistant
from app.multi_agent.assistants.runnable.trip_runnable import trip_assistant_runnable,trip_tools
from app.multi_agent.tools.base import create_tool_node_with_fallback
from app.multi_agent.workflow.base import split_tools,leave_skill
from typing import Callable, Literal
from app.multi_agent.assistants.data_model import CompleteOrEscalate
from app.multi_agent.state import CtripFlowState
from app.multi_agent.workflow.entry_node_producer import create_entry_node

TRIP_WRITE_TOOLS = ["book_excursion", "cancel_excursion", "update_excursion_details"]
trip_read_tools, trip_write_tools = split_tools(trip_tools, TRIP_WRITE_TOOLS)

def route_trip_assistant(state: CtripFlowState) -> Literal[
    "trip_read_tools",
    "trip_write_tools",
    "leave_skill",
    "__end__",]:
    """
    根据当前状态路由游览预订流程。

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
        if any(tc["name"] in TRIP_WRITE_TOOLS for tc in tool_calls):
            return "trip_write_tools"
        return "trip_read_tools"
    return "__end__"
    
def create_workflow(builder: StateGraph) -> StateGraph:
    """
    创建游览预订工作流
    """
    # 定义游览预订工作流
    builder.add_node("trip_entry", create_entry_node("游览预订助手", "trip_assistant"))
    builder.add_node("trip_assistant", Assistant(trip_assistant_runnable))
    builder.add_edge("trip_entry", "trip_assistant")

    builder.add_node("trip_read_tools", create_tool_node_with_fallback(trip_read_tools))
    builder.add_node("trip_write_tools", create_tool_node_with_fallback(trip_write_tools))
    builder.add_conditional_edges("trip_assistant", route_trip_assistant,
    ["trip_read_tools", "trip_write_tools", "leave_skill",END])
    builder.add_edge("trip_read_tools", "trip_assistant")
    builder.add_edge("trip_write_tools", "trip_assistant")
    return builder
