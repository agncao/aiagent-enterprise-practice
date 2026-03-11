from langgraph.graph import StateGraph
from app.multi_agent.state import CtripFlowState
from app.multi_agent.assistants.assistant import Assistant
from app.multi_agent.assistants.runnable.primary_runnable import primary_assistant_runnable,primary_assistant_tools
from app.multi_agent.tools.flight_tools import get_user_info
from app.multi_agent.workflow import car_rental_workflow,trip_workflow,hotel_workflow,flight_workflow
from app.multi_agent.tools.base import create_tool_node_with_fallback
from app.multi_agent.assistants.data_model import ToFlightBookingAssistant,ToBookCarRental,ToHotelBookingAssistant,ToBookExcursion
from langgraph.prebuilt import tools_condition
from langgraph.constants import START, END
from config import get_logger,CONFIG
from pathlib import Path
from langgraph.checkpoint.sqlite import SqliteSaver
from app.multi_agent.workflow.base import leave_skill
from langgraph.checkpoint.memory import MemorySaver


logger = get_logger(__name__)


def route_assistant(state: dict):
    """
    根据当前状态 判断路由到 子助手节点。
    :param state: 当前对话状态字典
    :return: 下一步应跳转到的节点名
    """
    route = tools_condition(state)  # 判断下一步的方向
    if route == END:
        return END  # 如果结束条件满足，则返回END
    tool_calls = state["messages"][-1].tool_calls  # 获取最后一条消息中的工具调用
    if tool_calls:
        if tool_calls[0]["name"] == ToFlightBookingAssistant.__name__:
            return "flight_entry"  # 跳转至航班预订入口节点
        elif tool_calls[0]["name"] == ToBookCarRental.__name__:
            return "car_rental_entry"  # 跳转至租车预订入口节点
        elif tool_calls[0]["name"] == ToHotelBookingAssistant.__name__:
            return "hotel_entry"  # 跳转至酒店预订入口节点
        elif tool_calls[0]["name"] == ToBookExcursion.__name__:
            return "trip_entry"  # 跳转至游览预订入口节点
        return "primary_assistant_tools"  # 否则跳转至主助理工具节点
    raise ValueError("无效的路由")  # 如果没有找到合适的工具调用，抛出异常

def route_to_sub_assistant(state: CtripFlowState) -> str:
    """
    根据当前状态路由到 子助手节点。

    :param state: 当前对话状态字典
    :return: 下一步应跳转到的节点名
    """
    dialog_list = state.get("dialog_state", [])
    logger.info(f"dialog_list: {dialog_list}")
    if not dialog_list:
        return "primary_assistant"
    return dialog_list[-1]

def build_primary_workflow():
    # 定义了一个流程图的构建对象
    builder = StateGraph(CtripFlowState)

    # 新增：fetch_user_info节点首先运行，这意味着我们的助手可以在不采取任何行动的情况下看到用户的航班信息
    builder.add_node('fetch_user_info', get_user_info)
    builder.add_edge(START, 'fetch_user_info')

    # 添加主助理
    builder.add_node('primary_assistant', Assistant(primary_assistant_runnable))
    builder.add_node(
        "primary_assistant_tools", create_tool_node_with_fallback(primary_assistant_tools)  # 主助理工具节点，包含各种工具
    )

    builder.add_node("leave_skill",leave_skill)
    builder.add_edge("leave_skill", "primary_assistant")
    
    # # 添加 四个业务助理 的 子工作流
    builder = hotel_workflow.create_workflow(builder)
    builder = flight_workflow.create_workflow(builder)
    builder = car_rental_workflow.create_workflow(builder)
    builder = trip_workflow.create_workflow(builder)

    builder.add_conditional_edges("primary_assistant", route_assistant,
        [
            "flight_entry", 
            "car_rental_entry", 
            "hotel_entry", 
            "trip_entry", 
            "primary_assistant_tools", 
            END])
    builder.add_edge("primary_assistant_tools", "primary_assistant")

    builder.add_conditional_edges("fetch_user_info", route_to_sub_assistant,
        [
            "flight_assistant", 
            "car_rental_assistant", 
            "hotel_assistant", 
            "trip_assistant", 
            "primary_assistant", 
            END])
    memory = MemorySaver()
    return builder.compile(
        checkpointer=memory,
        interrupt_before=[
            "hotel_write_tools",
            "flight_write_tools",
            "car_rental_write_tools",
            "trip_write_tools",
        ]
    )  
    # sqllite checkpoint
    # db_file = Path(CONFIG["graph"]["checkpointer"]["url"])
    # logger.info(f"db_file: {str(db_file)}")
    # with SqliteSaver.from_conn_string(CONFIG["graph"]["checkpointer"]["url"]) as checkpointer:
    #     return builder.compile(checkpointer=checkpointer)
