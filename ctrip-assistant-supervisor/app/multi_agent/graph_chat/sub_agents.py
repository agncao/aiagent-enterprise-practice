from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver

from app.multi_agent.llm import llm
from app.multi_agent.graph_chat.task_handoff import create_task_handoff_tool
from app.multi_agent.tools.policy_retriver import lookup_policy
from app.multi_agent.tools.car_rental_tools import (
    book_car_rental,
    cancel_car_rental,
    search_car_rentals,
    update_car_rental_dates,
)
from app.multi_agent.tools.flight_tools import (
    cancel_ticket,
    fetch_user_flight_information,
    search_flights,
    update_ticket_to_new_flight,
)
from app.multi_agent.tools.hotel_tools import (
    book_hotel,
    cancel_hotel,
    search_hotels,
    update_hotel_dates,
)
from app.multi_agent.tools.search_tool import tavily_tool
from app.multi_agent.tools.trip_recommendation_tools import (
    book_excursion,
    cancel_excursion,
    search_trip_recommendations,
    update_excursion_details,
)


def build_sub_agents(memory: InMemorySaver):
    return [
        create_agent(
        model=llm,
        tools=[search_car_rentals, book_car_rental, update_car_rental_dates, cancel_car_rental],
        name="car_rental_agent",
        checkpointer=memory,
        system_prompt=(
            "你是专门处理租车查询，租车预订，租车订单修改的智能体(Agent)。\n\n"
            "指令：\n"
            "- 在搜索时，请坚持不懈。如果第一次搜索没有结果，请扩大查询范围。\n"
            "- 根据用户的偏好搜索可用的租车服务，并与客户确认预订详情。\n"
            "- 如果您的工具都不适用或客户改变主意，直接回复，并给出理由。\n"
            "- 回复时仅包含工作结果，不要包含任何其他文字"
        ),
    ),
    create_agent(
        model=llm,
        tools=[search_hotels, book_hotel, update_hotel_dates, cancel_hotel],
        name="hotel_agent",
        checkpointer=memory,
        system_prompt=(
            "你是专门处理酒店查询，酒店预定，酒店订单修改的智能体(Agent)。\n\n"
            "指令：\n"
            "- 在搜索时，请坚持不懈。如果第一次搜索没有结果，请扩大查询范围。\n"
            "- 根据用户的偏好搜索可用酒店，并与客户确认预订详情。\n"
            "- 如果您的工具都不适用或客户改变主意，直接回复，并给出理由。\n"
            "- 回复时仅包含工作结果，不要包含任何其他文字"
        ),
    ),
    create_agent(
        model=llm,
        tools=[search_flights, fetch_user_flight_information, update_ticket_to_new_flight, cancel_ticket,lookup_policy],
        name="flight_agent",
        checkpointer=memory,
        system_prompt=(
            "你是专门处理航班查询，改签政策查询，改签和预定的智能体(Agent)。\n\n"
            "指令：\n"
            "- 在搜索航班时，请坚持不懈。如果第一次搜索没有结果，请扩大查询范围。\n"
            "- 如果您的工具都不适用或客户改变主意，直接回复，并给出理由。\n"
            "- 回复时仅包含工作结果，不要包含任何其他文字"
        ),
    ),
    create_agent(
        model=llm,
        tools=[search_trip_recommendations, book_excursion, update_excursion_details, cancel_excursion],
        name="trip_recommendation_agent",
        checkpointer=memory,
        system_prompt=(
            "你是专门处理旅行推荐查询，旅行产品预定，旅行订单修改的智能体(Agent)。\n\n"
            "指令：\n"
            "- 在搜索时，请坚持不懈。如果第一次搜索没有结果，请扩大查询范围。\n"
            "- 根据用户的偏好搜索可行的旅行推荐，并与客户确认预订详情。\n"
            "- 如果您的工具都不适用或客户改变主意，直接回复，并给出理由。\n"
            "- 回复时仅包含工作结果，不要包含任何其他文字"
        ),
    ),
    create_agent(
        model=llm,
        tools=[tavily_tool],
        name="tavily_search_agent",
        checkpointer=memory,
        system_prompt=(
            "你是一个网络搜索的智能体(Agent)。\n\n"
            "指令：\n"
            "- 仅网络数据获取、网络查询、数据查询相关的任务\n"
            "- 回复时仅包含工作结果，不要包含任何其他文字"
        ),
    )
    ]


