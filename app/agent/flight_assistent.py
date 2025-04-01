from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from typing_extensions import TypedDict, Annotated
from infrastructure.config import config
from service.flight_service import FlightService
from utils.langgraph_utils import *
import time
from langchain_core.runnables import Runnable,RunnablePassthrough, RunnableLambda
from langgraph.graph import add_messages, StateGraph, END
from langchain_core.tools import tool
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolNode

api_key = config.get('llm.api_key')
base_url = config.get('llm.base_url')
model_name = config.get('llm.model_name')

llm=ChatOpenAI(base_url=base_url,api_key=api_key,model_name=model_name, streaming=True)

class FlightState(TypedDict):
    messages: Annotated[list, add_messages]  # 存储对话上下文
    params: dict  # 存储航班查询参数
    input: str  # 添加input字段，用于存储用户输入
    result: list  # 存储工具执行结果
    params_ready: bool=False  # 存储参数是否准备好的标志

@tool
def check_params(state: FlightState) -> FlightState:
    """
    航班信息查询入参校验
    判断params字段是否准备好的条件：
    1. 查询state中的params字段departure_airport和destination_airport是否都不为空
    - 如果都不为空，则为True, 否则为False
    2. 查询state中的params字段departure_time或者arrival_time是否有值
    - 如果有值，且符合'yyyy-MM-dd hh:mm:ss' 格式 则为True, 否则为False
    3. 以上任何一个条件为Flase, 都会继续保留在agent节点
    4. 如果以上条件都为True, 则会执行下一个节点

    Args:
        state (FlightState): 当前状态
    Returns:
        str: 状态
    """
    params = state["params"]
    departure_airport = params.get("departure_airport")
    destination_airport = params.get("destination_airport")
    departure_time = params.get("departure_time")
    arrival_time = params.get("arrival_time")
    yes = departure_airport and destination_airport
    time_format = "%Y-%m-%d %H:%M:%S"
    if departure_time and arrival_time:
        try:
            time.strptime(departure_time, time_format)
            time.strptime(arrival_time, time_format)
            yes = True
        except ValueError:
            yes = False
    else:
        yes = False
    state["params_ready"] = yes
    return {
        "messages": ["参数校验通过"] if yes else ["参数校验失败"],
    }

# 修改工具配置
tools = [check_params,FlightService.search_flights]

def _get_system_prompt() -> str:
    """
    获取助理的提示词
    Returns:
        str: 提示词
    """
    return """
    你是一个航班助理，负责处理与航班和机票相关的业务。

    你需要从用户输入中提取以下信息并明确告知用户：
    1、起飞地(departure_airport): 必须是具体的机场或城市名
    2、目的地(destination_airport): 必须是具体的机场或城市名
    3、起飞时间(departure_time): 可选项，如果用户未指定，则为明天
    4、到达时间(arrival_time): 可选项，用户可能不会指定

    工作流程：
    1. 首先分析用户输入，提取或询问必要信息
    2. 确认信息完整性，如果信息不完整，请礼貌地询问缺失的信息
    3. 使用 search_flights 工具搜索符合条件的航班
    4. 向用户展示搜索结果

    注意事项：
    - 如果信息不完整，不要擅自假设或填充
    - 如果用户提供的信息模糊，要主动询问确认
    - 始终使用实际存在的机场或城市名
    - 对于时间信息，需要明确具体的日期和时间段
    """

def agent_node(state: FlightState) -> FlightState:
    """
    执行助理节点的逻辑
    - 执行航班信息查询入参校验工具
    - 如果入参校验通过，则执行search_flights工具查询航班信息
    - 如果入参校验不通过，则向用户请求缺失的信息
    Args:
        state (FlightState): 当前状态
    Returns:
        FlightState: 更新后的状态
    """
    print("agent_node start: FlightState = ",state)

    # 从state中提取用户输入和历史消息
    state["messages"].append(HumanMessage(content=state["input"]))    
    agent = _create_agent_executor(state)
    result = agent.invoke({"input": state["input"]})

    try:
        if hasattr(result, "tool_calls") and result.tool_calls:
            for tool_call in result.tool_calls:
                pass
                # print("Agent执行工具: ", tool_call.function.name)
        else:
            state["messages"].append(AIMessage(content=result.content))
    except Exception as e:
        print("Agent执行出错, state = ", state)
        raise e
    return state

def _create_agent_executor(state: FlightState) -> Runnable:
    """
    创建助理的代理执行器
    Returns:
        代理执行器
    """
    llm_with_tools = llm.bind_tools(tools=tools)
    prompt = ChatPromptTemplate.from_messages([
        ("system",_get_system_prompt()),
        MessagesPlaceholder(variable_name="history_messages"),
        ("user", "{input}"),
    ])

    input_dict = RunnablePassthrough.assign(
        history_messages=lambda x: state["messages"]
    )
    return input_dict|prompt | llm_with_tools

def check_tool_result(state: FlightState) -> str:
    """
    检查工具执行结果是否为空
    如果参数已准备好，返回"has_result"
    如果参数未准备好，返回"no_result"

    Args:
        state (FlightState): 当前状态
    Returns:
        str: 状态
    """
    if state["params_ready"]:
        return "has_result"
    return "no_result"

# 创建工作流
workflow = StateGraph(state_schema=FlightState)
tool_node = ToolNode(tools=tools)
# 添加节点
workflow.add_node("agent", agent_node)
workflow.add_node("tools", tool_node)

# 设置入口点
workflow.set_entry_point("agent")
workflow.add_edge("agent", "tools")

workflow.add_conditional_edges(
    "tools",
    check_tool_result,
    {
        "has_result": END,  # 如果找到航班结果，结束流程
        "no_result": "agent"  # 如果没找到航班，转到提示节点
    }
)
# 编译工作流
memory = MemorySaver()
app = workflow.compile(checkpointer=memory,interrupt_before=["tools"])


# 运行工作流
def run_assistant():
    print("如果需要退出，请输入'退出','quit','q','exit' 任意一项。")
    user_input = input("请输入您的航班查询需求: ")
    
    print("\n开始处理您的请求...\n")
    
    # 创建会话ID
    session_id = str(int(time.time()))
    config = {
        "configurable": {
            "thread_id": session_id
        }
    }
    
    # 对话历史
    messages = []
    
    while True:
        try:
            # 创建当前状态
            current_state = {
                "messages": messages,
                "params": {},
                "input": user_input,
                "result": None,
                "params_ready": False,
            }
            
            # 执行一次工作流
            result = app.invoke(current_state, config=config)
            
            # 更新消息历史
            if "messages" in result and result["messages"]:
                messages = result["messages"]
                
                # 找到最新的AI消息并显示
                for i in range(len(messages)-1, -1, -1):
                    if isinstance(messages[i], AIMessage):
                        print("\nAssistant:", messages[i].content)
                        break
            
            # 检查是否已完成查询
            if result.get("params_ready") and result.get("result"):
                print("\n查询结果为:", result["result"])
                break
                
            # 获取用户输入
            user_input = input("\n用户: ")
            if user_input.lower() in ["退出", "quit", "q", "exit"]:
                print("对话结束，拜拜！")
                break
                
        except Exception as e:
            print(f"发生错误: {str(e)}")
            # 出错时也给用户一次重新输入的机会
            user_input = input("\n发生错误，请重新输入或输入'退出'结束对话: ")
            if user_input.lower() in ["退出", "quit", "q", "exit"]:
                print("对话结束，拜拜！")
                break
            
if __name__ == "__main__":
    run_assistant()