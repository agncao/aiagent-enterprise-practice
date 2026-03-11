import uuid
from app.multi_agent.workflow.primary_workflow import build_primary_workflow
from app.multi_agent.workflow.init_db import update_dates
from langchain_core.messages import ToolMessage,AIMessage
from app.multi_agent.workflow.base import print_event

INTERRUPT_NODES = {
    "hotel_write_tools",
    "flight_write_tools",
    "car_rental_write_tools",
    "trip_write_tools",
}

if __name__ == "__main__":
    update_dates()
    graph = build_primary_workflow()

    # draw = graph.get_graph(xray=True)
    # draw.draw_mermaid_png(output_file_path="ctrip_workflow1.png")

    session_id=str(uuid.uuid4())
    config = {
        "configurable": {
            # passenger_id用于我们的航班工具，以获取用户的航班信息
            "passenger_id": "3442 587242",
            # 检查点由session_id访问
            "thread_id": session_id,
        }
    }

    _printed = set()
    while True:
        user_input = input("用户: ")
        if user_input.lower() in ["exit", "quit", "q"]:
            break
        try:
            events = graph.stream(
                {"messages": [("user", user_input)]},
                config=config,
                stream_mode="updates",
            )
            for event in events:
                print_event(event, _printed)

            current_state = graph.get_state(config)
            pending_nodes = set(current_state.next or ())
            if pending_nodes & INTERRUPT_NODES:
                tool_call_id = current_state.values["messages"][-1].tool_calls[0]["id"]
                approval = input("您是否批准上述操作？输入'y'继续；否则，请说明您请求的更改。\n")
                if approval.strip().lower() == "y":
                    events = graph.stream(None, config=config, stream_mode="updates")
                    for event in events:
                        print_event(event, _printed)
                else:
                    events = graph.stream(
                        {
                            "messages": [
                                ToolMessage(
                                    role="tool",
                                    tool_call_id=tool_call_id,
                                    content=f"Tool的调用被用户拒绝。原因：'{approval}'。",
                                )
                            ]
                        },
                        config,
                        stream_mode="updates",
                    )
                    for event in events:
                        print_event(event, _printed)
        except Exception as e:
            raise e
