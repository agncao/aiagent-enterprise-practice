from app.multi_agent.tools.user_info import get_user_info
from langgraph.graph import START, StateGraph, END
from app.multi_agent.graph_chat.supervisor import build_supervisor
from app.multi_agent.graph_chat.sub_agents import build_sub_agents
from app.multi_agent.graph_chat.state import CtripFlowState
from IPython.display import display, Image
from langgraph.checkpoint.memory import InMemorySaver

memorySaver = InMemorySaver()

car_rental_agent, hotel_agent, flight_agent, trip_recommendation_agent, tavily_search_agent = build_sub_agents(memorySaver)
supervisor = build_supervisor(memorySaver)
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
    .compile(checkpointer=memorySaver)
)


# 生成图片的二进制数据
png_bytes = workflow.get_graph().draw_mermaid_png()

# 指定文件名并保存到本地
file_name = "workflow_supervisor_graph.png"
with open(file_name, "wb") as f:
    f.write(png_bytes)

# 在 Jupyter 环境中显示保存的图片
display(Image(filename=file_name))