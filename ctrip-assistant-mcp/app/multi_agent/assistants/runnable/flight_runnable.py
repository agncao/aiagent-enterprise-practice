from app.multi_agent.tools.flight_tools import (
    fetch_user_flight_information,
    search_flights,
    update_ticket_to_new_flight,
    cancel_ticket,
)
from app.multi_agent.assistants.prompts import (
    FLIGHT_ASSISTANT_PROMPT,
)
from app.multi_agent.assistants.data_model import (
    CompleteOrEscalate,
)
from app.multi_agent.assistants.llm import llm


# Flight Assistant
flight_tools = [
    search_flights,
    fetch_user_flight_information,
    update_ticket_to_new_flight,
    cancel_ticket,
]
flight_assistant_runnable = FLIGHT_ASSISTANT_PROMPT | llm.bind_tools(flight_tools + [CompleteOrEscalate])
