# app/agent/executor.py (修正拼写)
from agent.router import AssistantRouter
from agent.flight.flight_assistant import FlightAssistant
# 未来会导入其他助理
# from agent.hotel.hotel_assistant import HotelAssistant
# from agent.car.car_assistant import CarAssistant

class AssistantExecutor:
    def __init__(self, llm):
        self.instance = AssistantRouter.create_assistant("flight")


# # app/agent/executor.py (修正拼写)
# from agent.router import AssistantRouter
# from agent.flight.flight_assistant import FlightAssistant
# # 未来会导入其他助理
# # from agent.hotel.hotel_assistant import HotelAssistant
# # from agent.car.car_assistant import CarAssistant

# class AssistantExecutor:
#     def __init__(self, llm):
#         self.router = AssistantRouter(llm)
#         self._register_assistants()
    
#     def _register_assistants(self):
#         """注册所有可用的助理"""
#         self.router.register_assistant("flight", FlightAssistant, is_default=True)
#         # 未来会注册其他助理
#         # self.router.register_assistant("hotel", HotelAssistant)
#         # self.router.register_assistant("car", CarAssistant)
    
#     def execute(self, user_input):
#         """执行用户请求"""
#         assistant = self.router.route_request(user_input)
#         return assistant.run_assistant()