from app.multi_agent.tools.search_tool import tavily_tool
from app.multi_agent.tools.policy_retriver import lookup_policy
from app.multi_agent.assistants.data_model import (
    ToBookCarRental,
    ToBookExcursion,
    ToFlightBookingAssistant,
    ToHotelBookingAssistant,
)
from app.multi_agent.assistants.prompts import PRIMARY_ASSISTANT_PROMPT
from app.multi_agent.assistants.llm import llm

# Primary Assistant
primary_assistant_tools = [
    tavily_tool,
    lookup_policy,
]
primary_assistant_runnable = PRIMARY_ASSISTANT_PROMPT | llm.bind_tools(
    primary_assistant_tools + [
        ToFlightBookingAssistant,  # 用于转交航班更新或取消的任务
        ToBookCarRental,  # 用于转交租车预订的任务
        ToHotelBookingAssistant,  # 用于转交酒店预订的任务
        ToBookExcursion,  # 用于转交旅行推荐和其他游览预订的任务
    ]
)