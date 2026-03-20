from typing import Annotated

from langchain_core.messages import ToolMessage
from langchain_core.tools import BaseTool, InjectedToolCallId, tool
from langgraph.prebuilt import InjectedState
from langgraph.types import Command


def create_task_handoff_tool(
    *,
    agent_name: str,
    description: str | None = None,
) -> BaseTool:
    """
    创建一个用于将当前会话转接到指定代理的工具函数。

    该函数返回一个装饰器包装的工具函数，当调用时会生成一个工具消息并返回转接命令，
    指示流程控制器将控制权转移给指定的代理。

    参数:
        agent_name (str): 目标代理的名称，用于标识要转接的代理
        description (str | None): 工具的描述信息，如果未提供则使用默认描述

    返回:
        handoff_tool: 一个装饰器包装的工具函数，用于执行转接操作
    """
    tool_name = f"transfer_to_{agent_name}"
    tool_description = description or f"将任务交接给 {agent_name}"

    @tool(tool_name, description=tool_description)
    def handoff_tool(
        state: Annotated[dict, InjectedState],
        tool_call_id: Annotated[str, InjectedToolCallId],
    ) -> Command:
        messages = list(state.get("messages", []))
        handoff_msg = ToolMessage(
            content=f"已交接给 {agent_name}",
            name=tool_name,
            tool_call_id=tool_call_id,
        )

        return Command(
            goto=agent_name,
            graph=Command.PARENT,
            update={**state,"messages": messages + [handoff_msg]},
        )

    return handoff_tool


def build_handoff_tools() -> list[BaseTool]:
    return [
        create_task_handoff_tool(
            agent_name="car_rental_agent",
            description="将任务交接给租车服务智能体",
        ),
        create_task_handoff_tool(
            agent_name="hotel_agent",
            description="将任务交接给酒店智能体",
        ),
        create_task_handoff_tool(
            agent_name="flight_agent",
            description="将任务交接给航班预订智能体",
        ),
        create_task_handoff_tool(
            agent_name="trip_recommendation_agent",
            description="将任务交接给旅行景点推荐智能体",
        ),
        create_task_handoff_tool(
            agent_name="tavily_search_agent",
            description="将任务交接给网络搜索智能体",
        ),
    ]