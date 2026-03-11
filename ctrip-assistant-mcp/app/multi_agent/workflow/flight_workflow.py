from langgraph.constants import END
from langgraph.graph import StateGraph
from langgraph.prebuilt import tools_condition
from app.multi_agent.assistants.assistant import Assistant
from app.multi_agent.assistants.runnable.flight_runnable import flight_assistant_runnable,flight_tools
from app.multi_agent.tools.base import create_tool_node_with_fallback
from app.multi_agent.workflow.base import split_tools,leave_skill
from typing import Callable, Literal
from app.multi_agent.assistants.data_model import CompleteOrEscalate
from app.multi_agent.state import CtripFlowState
from app.multi_agent.workflow.entry_node_producer import create_entry_node

FLIGHT_WRITE_TOOLS = ["update_ticket_to_new_flight", "cancel_ticket"]
flight_read_tools, flight_write_tools = split_tools(flight_tools, FLIGHT_WRITE_TOOLS)

def route_flight_assistant(state: CtripFlowState) -> Literal[
    "flight_read_tools",
    "flight_write_tools",
    "leave_skill",
    "__end__",]:
    """
    根据当前状态路由航班更新流程。

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
        if any(tc["name"] in FLIGHT_WRITE_TOOLS for tc in tool_calls):
            return "flight_write_tools"
        return "flight_read_tools"
    return "__end__"
        
def create_workflow(builder: StateGraph) -> StateGraph:
    """
    创建航班工作流
    """
    # 定义航班工作流
    builder.add_node("flight_entry", create_entry_node("航班助手", "flight_assistant"))
    builder.add_node("flight_assistant", Assistant(flight_assistant_runnable))
    builder.add_edge("flight_entry", "flight_assistant")

    builder.add_node("flight_read_tools", create_tool_node_with_fallback(flight_read_tools))
    builder.add_node("flight_write_tools", create_tool_node_with_fallback(flight_write_tools))
    builder.add_conditional_edges("flight_assistant", route_flight_assistant,
    ["flight_write_tools", "flight_read_tools", "leave_skill",END])
    builder.add_edge("flight_write_tools", "flight_assistant")
    builder.add_edge("flight_read_tools", "flight_assistant")

    return builder
