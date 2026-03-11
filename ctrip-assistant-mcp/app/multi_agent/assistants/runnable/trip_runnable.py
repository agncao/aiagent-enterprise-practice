
from app.multi_agent.tools.trip_recommendation_tools import (
    search_trip_recommendations,
    book_excursion,
    update_excursion_details,
    cancel_excursion,
)
from app.multi_agent.assistants.prompts import (
    TRIP_RECOMMENDATION_ASSISTANT_PROMPT,
)
from app.multi_agent.assistants.data_model import (
    CompleteOrEscalate,
)
from app.multi_agent.assistants.llm import llm


# Trip Recommendation Assistant
trip_tools = [
    search_trip_recommendations,
    book_excursion,
    update_excursion_details,
    cancel_excursion,
]
trip_assistant_runnable = TRIP_RECOMMENDATION_ASSISTANT_PROMPT | llm.bind_tools(trip_tools + [CompleteOrEscalate])