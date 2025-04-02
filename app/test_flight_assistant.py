from app.agent.router import AssistantRouter
from app.agent.assistant_type import AssistantType

def main():
    """测试航班助理"""
    
    # 构建并运行助理
    flight_assistant = AssistantRouter.create_assistant(AssistantType.FLIGHT)
    flight_assistant.run_assistant()

if __name__ == "__main__":
    main()
