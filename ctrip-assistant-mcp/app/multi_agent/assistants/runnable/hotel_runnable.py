from app.multi_agent.tools.hotel_tools import (
    search_hotels,
    book_hotel,
    cancel_hotel,
    update_hotel_dates,
)
from app.multi_agent.assistants.prompts import (
    HOTEL_ASSISTANT_PROMPT,
)
from app.multi_agent.assistants.data_model import (
    CompleteOrEscalate,
)
from app.multi_agent.assistants.llm import llm

# Hotel Assistant
hotel_tools = [
    search_hotels,
    book_hotel,
    cancel_hotel,
    update_hotel_dates,
]
hotel_assistant_runnable = HOTEL_ASSISTANT_PROMPT | llm.bind_tools(hotel_tools + [CompleteOrEscalate])
