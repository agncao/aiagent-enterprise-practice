
from app.multi_agent.tools.car_rental_tools import (
    search_car_rentals,
    book_car_rental,
    update_car_rental_dates,
    cancel_car_rental,
)
from app.multi_agent.assistants.prompts import (
    CAR_RENTAL_ASSISTANT_PROMPT,
)
from app.multi_agent.assistants.data_model import (
    CompleteOrEscalate,
)
from app.multi_agent.assistants.llm import llm


# Car Rental Assistant
car_rental_tools = [
    search_car_rentals,
    book_car_rental,
    update_car_rental_dates,
    cancel_car_rental,
]
car_rental_assistant_runnable = CAR_RENTAL_ASSISTANT_PROMPT | llm.bind_tools(car_rental_tools + [CompleteOrEscalate])
