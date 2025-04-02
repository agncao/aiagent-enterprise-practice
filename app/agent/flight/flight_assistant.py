from langgraph import graph
from app.agent.state import State
from infrastructure.config import config
from service.flight_service import FlightService
from utils.langgraph_utils import *
import time
from langgraph.graph import StateGraph, END
from langchain_core.tools import tool
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolNode
from app.agent.base_assistant import BaseAssistant
from app.agent.assistant_type import AssistantType

class FlightAssistant(BaseAssistant):
    def __init__(self, llm):
        super().__init__(llm)
        self.tools = [self.check_params, FlightService.search_flights]
        self.state["assistant_type"] = AssistantType.FLIGHT

    def get_system_prompt(self) -> str:
        """
        获取助理的提示词
        Returns:
            str: 提示词
        """
        return """
            你是一个航班助理，负责处理与航班和机票相关的业务。

            你需要从用户输入中提取以下信息并明确告知用户：
            1、起飞地(departure_airport): 必须是具体的机场或城市名
            2、目的地(destination_airport): 必须是具体的机场或城市名
            3、起飞时间(departure_time): 可选项，如果用户未指定，则为明天
            4、到达时间(arrival_time): 可选项，用户可能不会指定

            工作流程：
            1. 首先分析用户输入，提取或询问必要信息
            2. 确认信息完整性，如果信息不完整，请礼貌地询问缺失的信息
            3. 使用 search_flights 工具搜索符合条件的航班
            4. 向用户展示搜索结果

            注意事项：
            - 如果信息不完整，不要擅自假设或填充
            - 如果用户提供的信息模糊，要主动询问确认
            - 始终使用实际存在的机场或城市名
            - 对于时间信息，需要明确具体的日期和时间段
        """

    @tool
    def check_params(state: State) -> dict:
        """
        航班信息查询入参校验
        判断params字段是否准备好的条件：
        1. 查询state中的params字段departure_airport和destination_airport是否都不为空
        - 如果都不为空，则为True, 否则为False
        2. 查询state中的params字段departure_time或者arrival_time是否有值
        - 如果有值，且符合'yyyy-MM-dd hh:mm:ss' 格式 则为True, 否则为False
        3. 以上任何一个条件为Flase, 都会继续保留在agent节点
        4. 如果以上条件都为True, 则会执行下一个节点

        Args:
            state (State): 当前状态
        Returns:
            dict: 包含params_ready字段的字典
        """
        params = state["params"]
        departure_airport = params.get("departure_airport")
        destination_airport = params.get("destination_airport")
        departure_time = params.get("departure_time")
        arrival_time = params.get("arrival_time")
        yes = departure_airport and destination_airport
        time_format = "%Y-%m-%d %H:%M:%S"
        if departure_time and arrival_time:
            try:
                time.strptime(departure_time, time_format)
                time.strptime(arrival_time, time_format)
                yes = True
            except ValueError:
                yes = False
        else:
            yes = False
        state["params_ready"] = yes
        return {
            "messages": ["参数校验通过"] if yes else ["参数校验失败"],
        }

    def check_tool_result(self, state: State) -> str:
        """
        检查工具执行结果是否为空
        如果参数已准备好，返回"has_result"
        如果参数未准备好，返回"no_result"

        Args:
            state (State): 当前状态
        Returns:
            str: 状态
        """
        if state["params_ready"]:
            return "has_result"
        return "no_result"
    
    def build(self):
        """构建助理的工作流"""
        # 创建工作流
        workflow = StateGraph(state_schema=State)
        tool_node = ToolNode(tools=self.tools)
        # 添加节点
        workflow.add_node("agent", self.agent_node)
        workflow.add_node("tools", tool_node)

        # 设置入口点
        workflow.set_entry_point("agent")
        workflow.add_edge("agent", "tools")

        workflow.add_conditional_edges(
            "tools",
            self.check_tool_result,
            {
                "has_result": END,  # 如果找到航班结果，结束流程
                "no_result": "agent"  # 如果没找到航班，转到提示节点
            }
        )
        # 编译工作流
        memory = MemorySaver()
        self.worker = workflow.compile(checkpointer=memory, interrupt_before=["tools"])
        return self.worker
    
    def initial_state(self):
        """初始化状态"""
        return {
            "messages": [],
            "params": {},
            "input": "",
            "result": None,
            "params_ready": False,
            "assistant_name": self.__class__.__name__,
            "assistant_type": AssistantType.FLIGHT
        }
