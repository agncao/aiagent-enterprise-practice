from langgraph.constants import END
from langgraph.graph import StateGraph
from langgraph.prebuilt import tools_condition

from app.multi_agent.assistants.assistant import Assistant
from app.multi_agent.assistants.runnable.car_rental_runnable import car_rental_assistant_runnable,car_rental_tools
from app.multi_agent.tools.base import create_tool_node_with_fallback
from app.multi_agent.workflow.base import split_tools,leave_skill
from typing import Callable, Literal
from app.multi_agent.assistants.data_model import CompleteOrEscalate
from app.multi_agent.state import CtripFlowState
from app.multi_agent.workflow.entry_node_producer import create_entry_node


CAR_WRITE_TOOLS = ["book_car_rental", "update_car_rental_dates", "cancel_car_rental"]
car_rental_read_tools, car_rental_write_tools = split_tools(car_rental_tools, CAR_WRITE_TOOLS)

def route_car_assistant(state: CtripFlowState) -> Literal[
    "car_rental_read_tools",
    "car_rental_write_tools",
    "leave_skill",
    "__end__",]:
    """
    根据当前状态路由汽车租赁更新流程。

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
        if any(tc["name"] in CAR_WRITE_TOOLS for tc in tool_calls):
            return "car_rental_write_tools"
        return "car_rental_read_tools"
    return END
    
def create_workflow(builder: StateGraph) -> StateGraph:
    """
    创建汽车租赁工作流
    """
    # 定义汽车租赁工作流
    builder.add_node("car_rental_entry", create_entry_node("汽车租赁助手", "car_rental_assistant"))
    builder.add_node("car_rental_assistant", Assistant(car_rental_assistant_runnable))
    builder.add_edge("car_rental_entry", "car_rental_assistant")

    builder.add_node("car_rental_read_tools", create_tool_node_with_fallback(car_rental_read_tools))
    builder.add_node("car_rental_write_tools", create_tool_node_with_fallback(car_rental_write_tools))
    builder.add_conditional_edges("car_rental_assistant", route_car_assistant,
    ["car_rental_read_tools", "car_rental_write_tools", "leave_skill",END])

    builder.add_edge("car_rental_read_tools", "car_rental_assistant")
    builder.add_edge("car_rental_write_tools", "car_rental_assistant")
    return builder
