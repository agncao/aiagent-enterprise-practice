from certifi import contents
from langchain_core.messages import AIMessage
from typing_extensions import override
from langgraph import graph
from app.agent.state import State
from infrastructure.config import config
from service.flight_service import FlightService
import time
from langgraph.graph import StateGraph, END
from langchain_core.tools import tool
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolNode
from app.agent.base_assistant import BaseAssistant
from app.agent.assistant_type import AssistantType
from infrastructure.logger import log

class FlightAssistant(BaseAssistant):
    def __init__(self, llm):
        super().__init__(llm)
        self.tools = [self.check_params, FlightService.search_flights]
        self.state["assistant_type"] = AssistantType.FLIGHT
        self.state["params"] = {}

    def get_system_prompt(self):
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
            3. 使用 check_params 工具检查参数是否完整
            4. 如果参数完整，使用 search_flights 工具搜索符合条件的航班
            5. 向用户展示搜索结果

            注意事项：
            - 如果信息不完整，不要擅自假设或填充
            - 如果用户提供的信息模糊，要主动询问确认
            - 始终使用实际存在的机场或城市名
            - 对于时间信息，需要明确具体的日期和时间段
            
            你必须使用提供的工具来完成任务：
            1. 当用户提供了起飞地和目的地信息时，必须调用 check_params 工具检查参数是否完整
            2. 当参数检查通过后，必须调用 search_flights 工具搜索航班
            
            不要尝试自己计算或判断，必须使用工具来完成这些任务。
            
            重要提示：对于任何用户输入，无论内容如何，你都必须首先调用 check_params 工具来检查和提取可能的参数。
        """

    @tool
    def check_params(self, state: State):
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
        log.debug("执行 check_params 工具，当前状态: {}", state)
        params = state["params"] or {}
        departure_airport = params.get("departure_airport")
        destination_airport = params.get("destination_airport")
        departure_time = params.get("departure_time")
        arrival_time = params.get("arrival_time")
        
        # 检查起飞地和目的地是否都存在
        params_ready = departure_airport and destination_airport
        
        # 如果起飞地和目的地都存在，检查时间格式
        if params_ready and (departure_time or arrival_time):
            time_format = "%Y-%m-%d %H:%M:%S"
            try:
                if departure_time:
                    time.strptime(departure_time, time_format)
                if arrival_time:
                    time.strptime(arrival_time, time_format)
                # 时间格式正确，参数准备就绪
            except ValueError:
                # 时间格式错误，参数未准备就绪
                params_ready = False
                return {
                    "messages": [AIMessage(content="请提供正确格式的时间信息，格式应为'yyyy-MM-dd'，例如'2025-04-03'。")]
                }
        
        state["params_ready"] = params_ready
        # 生成用户友好的提示消息
        from langchain_core.messages import AIMessage
        
        if params_ready:
            return {
                "messages": [AIMessage(content=f"我已确认您的航班查询信息：从{departure_airport}到{destination_airport}。正在为您搜索航班...")]
            }
        else:
            # 根据不同的缺失参数情况，生成针对性的提示消息
            if not departure_airport and not destination_airport:
                # 两个参数都缺失
                message = "您好，请告诉我您想查询从哪个城市到哪个城市的航班？"
            elif not departure_airport:
                # 只缺少起飞地
                message = f"好的，请问您从哪个城市出发？"
            elif not destination_airport:
                # 只缺少目的地
                message = f"好的，请问您想前往哪个城市？"
            else:
                message = "你想什么时候出发呢？"
            
            return {
                "messages": [AIMessage(content=message)]
            }

    def _check_tool_result(self, state: State):
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
            self._check_tool_result,
            {
                "has_result": END,  # 如果找到航班结果，结束流程
                "no_result": "agent"  # 如果没找到航班，转到提示节点
            }
        )
        # 编译工作流
        memory = MemorySaver()
        self.worker = workflow.compile(checkpointer=memory, interrupt_before=["tools"])
        return self.worker