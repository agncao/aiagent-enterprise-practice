from app.multi_agent.tools.user_info import get_user_info
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, StateGraph, END
from app.multi_agent.graph_chat.supervisor import build_supervisor
from app.multi_agent.graph_chat.sub_agents import build_sub_agents
from app.multi_agent.graph_chat.state import CtripFlowState


car_rental_agent, hotel_agent, flight_agent, trip_recommendation_agent, tavily_search_agent = build_sub_agents()

memory = MemorySaver()

supervisor = build_supervisor()
workflow = (
    StateGraph(CtripFlowState)
    .add_node("fetch_user_info", get_user_info)
    .add_node("supervisor", supervisor, destinations=(
        "car_rental_agent",
        "hotel_agent",
        "flight_agent",
        "trip_recommendation_agent",
        "tavily_search_agent",
        END,
    ))
    .add_node("hotel_agent", hotel_agent, destinations=(END,))
    .add_node("flight_agent", flight_agent, destinations=(END,))
    .add_node("trip_recommendation_agent", trip_recommendation_agent, destinations=(END,))
    .add_node("car_rental_agent", car_rental_agent, destinations=(END,))
    .add_node("tavily_search_agent", tavily_search_agent, destinations=(END,))
    .add_edge(START, "fetch_user_info")
    .add_edge("fetch_user_info", "supervisor")
    .compile(checkpointer=memory)
)