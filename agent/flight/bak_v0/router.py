from agent.assistant_type import AssistantType
from infrastructure.config import config
from langchain_openai import ChatOpenAI

class AssistantRouter:
    """
    助理路由器，负责创建和路由不同类型的助理
    """
    
    @staticmethod
    def create_assistant(assistant_type):
        """
        根据助理类型创建对应的助理实例
        
        Args:
            assistant_type: 助理类型，可以是 AssistantType 枚举或字符串
            
        Returns:
            对应类型的助理实例
        """
        # 如果传入的是字符串，转换为枚举类型
        if isinstance(assistant_type, str):
            assistant_type = AssistantType.from_string(assistant_type)
            
        # 获取 LLM 配置
        api_key = config.get('llm.api_key')
        base_url = config.get('llm.base_url')
        model_name = config.get('llm.model_name')
        
        # 创建 LLM 实例
        llm = ChatOpenAI(base_url=base_url, api_key=api_key, model_name=model_name, streaming=True)
        
        # 根据助理类型创建对应的助理实例
        if assistant_type == AssistantType.FLIGHT:
            from agent.flight.flight_assistant import FlightAssistant
            return FlightAssistant(llm)
        elif assistant_type == AssistantType.HOTEL:
            # 未来实现
            # from agent.hotel.hotel_assistant import HotelAssistant
            # return HotelAssistant(llm)
            raise NotImplementedError("Hotel assistant not implemented yet")
        elif assistant_type == AssistantType.CAR:
            # 未来实现
            # from agent.car.car_assistant import CarAssistant
            # return CarAssistant(llm)
            raise NotImplementedError("Car assistant not implemented yet")
        else:
            raise ValueError(f"Unknown assistant type: {assistant_type}")
    

#     # app/agent/router.py
# class AssistantRouter:
#     def __init__(self, llm):
#         self.llm = llm
#         self.assistants = {}
#         self.default_assistant = None
    
#     def register_assistant(self, assistant_name, assistant_class, is_default=False):
#         """注册一个助理"""
#         self.assistants[assistant_name] = assistant_class
#         if is_default:
#             self.default_assistant = assistant_name
    
#     def route_request(self, user_input):
#         """根据用户输入路由到合适的助理"""
#         # 使用LLM分析用户需求，确定应该使用哪个助理
#         assistant_name = self._determine_assistant(user_input)
#         return self._create_assistant_instance(assistant_name)
    
#     def _determine_assistant(self, user_input):
#         """使用LLM确定用户需要哪种类型的助理"""
#         # 实现分类逻辑
#         pass
    
#     def _create_assistant_instance(self, assistant_name):
#         """创建并返回助理实例"""
#         if assistant_name in self.assistants:
#             return self.assistants[assistant_name](self.llm, State())
#         return self.assistants[self.default_assistant](self.llm, State())