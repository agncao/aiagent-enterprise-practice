from datetime import datetime
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from langchain_core.runnables import RunnablePassthrough
from langgraph.prebuilt import ToolNode
from app.utils.base_state import StateUtils
from infrastructure.config import config
from app.utils.langgraph_utils import loop_graph_invoke_tools, parse_output,loop_graph_invoke, get_answer
from infrastructure.logger import log
from app.agent.state import BaseState
import re

# ---------------------------
# 1. 定义数据模型和工具
# ---------------------------

class FlightParams(BaseModel):
    departure: str = Field(description="出发地，例如：北京")
    arrival: str = Field(description="抵达地，例如：上海")
    date: str = Field(description="出发日期（YYYY-MM-DD），例如：2024-03-20")

class AgentState(BaseState):
    timestamp: float  # 时间戳作为thread_id
    _complete: bool = False


# 初始化内存检查点（带自动清理）
memory = MemorySaver()  # 每100次操作清理一次旧数据

# 工具定义
@tool("check_params", args_schema=FlightParams)
def check_params(departure: str = None, arrival: str = None, date: str = None):
    """
    根据当前已收集参数检查完整性，自动识别缺失字段。
    当用户提供新信息时自动触发检查。
    """
    params = {"departure": departure, "arrival": arrival, "date": date}
    missing = [k for k, v in params.items() if not v]
    
    # 生成用户友好的提示消息
    if missing:
        if "departure" in missing and "arrival" in missing:
            message = "请提供起飞地和目的地信息。"
        elif "departure" in missing:
            message = f"已知目的地是{arrival}，请提供起飞地信息。"
        elif "arrival" in missing:
            message = f"已知起飞地是{departure}，请提供目的地信息。"
        else:
            message = f"请提供出发日期，格式为YYYY-MM-DD。"
        
        return {"status": "missing", "missing": missing, "message": message}
    
    return {"status": "complete", "params": params}

@tool("search_flights")
def search_flights(departure: str, arrival: str, date: str):
    """
    根据起飞地、目的地和日期搜索航班信息
    """
    # 模拟航班搜索结果
    flights = [
        {"flight_no": "CA1234", "departure": departure, "arrival": arrival, "date": date, "time": "08:00-10:00", "price": 1200},
        {"flight_no": "MU5678", "departure": departure, "arrival": arrival, "date": date, "time": "12:00-14:00", "price": 1500},
        {"flight_no": "CZ9012", "departure": departure, "arrival": arrival, "date": date, "time": "16:00-18:00", "price": 1100}
    ]
    return {"status": "success", "flights": flights}

# LLM配置
llm = ChatOpenAI(
    base_url=config.get("llm.base_url"),
    api_key=config.get("llm.api_key"),
    model_name=config.get("llm.model_name"),
    streaming=True
)

# 工具列表
tools = [check_params, search_flights]

# ---------------------------
# 3. 构建带检查点的工作流
# ---------------------------

def create_agent_executor():
    """
    代理节点，处理用户输入，调用LLM生成回复
    
    Args:
        state (AgentState): 当前状态
    
    Returns:
    """
    
    # 提示模板
    prompt = ChatPromptTemplate.from_messages([
        ("system", """
        你是一个航班助理，负责处理与航班和机票相关的业务。
        
        你需要从用户输入中提取以下信息：
        1、起飞地(departure): 必须是具体的机场或城市名
        2、目的地(arrival): 必须是具体的机场或城市名
        3、出发日期(date): 格式为YYYY-MM-DD
        
        工作流程：
        1. 首先分析用户输入，提取或询问必要信息
        2. 确认信息完整性，如果信息不完整，请礼貌地询问缺失的信息
        3. 使用 check_params 工具检查参数是否完整
        4. 如果参数完整，使用 search_flights 工具搜索符合条件的航班
        5. 向用户展示搜索结果
        
        重要提示：对于任何用户输入，无论内容如何，你都必须首先调用 check_params 工具来检查和提取可能的参数。
        不要尝试自己计算或判断，必须使用工具来完成这些任务。
        已收集参数：{collected_params}
        """),
        MessagesPlaceholder(variable_name="history_messages"),
        ("human", "{user_input}"),
        MessagesPlaceholder(variable_name="collected_params")
    ])
    
    # 绑定工具到LLM
    llm_with_tools = llm.bind_tools(tools=tools, tool_choice="auto")
    def agent_node(state: AgentState):
        try:
            # 运行链
            chain = RunnablePassthrough.assign(
                history_messages=lambda x: state["messages"],
                collected_params=lambda x: state["collected_params"]
            ) | prompt | llm_with_tools | parse_output
            response = chain.invoke({"user_input": state["user_input"]})
            response["_complete"] = False   # 给初始值：默认未完成
            if not (StateUtils.ready_call_tool(response)):
                response["_complete"] = True
            log.debug("LLM响应: {}", response)
        except Exception as e:
            log.error("代理执行出错: {}", str(e))
            raise e
        return response  # 添加这行，返回响应

    return agent_node

# 工具结果处理节点
def tool_result_node(state: AgentState):
    """
    处理工具执行结果
    
    Args:
        state (AgentState): 当前状态
    
    Returns:
        dict: 更新后的状态
    """
    log.debug("进入tool_result_node，当前状态: {}", state)

    # 从state的messages中取出最后一条，并判断是否toolmessage
    messages = state.get("messages", [])
    if messages and isinstance(messages[-1], ToolMessage):
        # 如果是ToolMessage，则直接返回其内容
        tool_message = messages[-1]
        if tool_message.status == "error":
            return {
                "messages": [AIMessage(content=tool_message.content)],
                "_complete": False  # 继续对话流程
            }
        else:
            return {
                "messages": [AIMessage(content=tool_message.content)],
                "_complete": True  # 完成
            }
    return {
        "messages": [AIMessage(content=f"工具无返回结果，tool_name: {state['tool_name']}，tool_args: {state['tool_args']} ")],
        "_complete": False  # 继续对话流程
    }

def parse_user_input(text: str) -> dict:
    """增强型参数解析（示例）"""
    patterns = {
        "departure": r"出发地[:：]?\s*(\S+)",
        "arrival": r"抵达地[:：]?\s*(\S+)",
        "date": r"日期[:：]?\s*(\d{4}-\d{2}-\d{2})"
    }
    return {k: re.search(v, text).group(1) for k, v in patterns.items() if re.search(v, text)}

def process_input_node(state: AgentState):
    """
    处理用户输入节点，提取参数:
    1. 如果没有提取到参数，则给出友好提示，继续对话流程
    2. 如果提取到参数，则调用check_params工具
    
    Args:
        state (AgentState): 当前状态
    
    Returns:
        dict: 更新后的状态
    """
    # 确保消息列表存在
    if "messages" not in state:
        state["messages"] = []
    
    # 确保collected_params字段存在，修改为列表
    if "collected_params" not in state:
        state["collected_params"] = []
    
    # 解析用户输入
    try:
        if state["user_input"]:
            new_params = parse_user_input(state["user_input"])
            
            # 更新收集的参数 - 这里需要修改，因为现在是列表而不是字典
            # 可以将新参数作为消息添加到列表中
            if new_params:
                from langchain_core.messages import SystemMessage
                param_message = SystemMessage(content=str(new_params))
                state["collected_params"].append(param_message)
    except Exception as e:
        log.error("解析用户输入出错: {}", str(e))
    
    # 返回更新后的状态
    return state

def check_completion(state: AgentState):
    """
    检查是否完成
    
    Args:
        state (AgentState): 当前状态
    
    Returns:
        str: 下一个节点的名称
    """
    # 如果已完成，则结束
    if state.get("_complete", False):
        return "end"
    
    if(StateUtils.ready_call_tool(state) and state["tool_name"] in ["check_params", "search_flights"]):
        return "tool"
    return "agent"

# 构建工作流
workflow = StateGraph(AgentState)

# 添加节点
agent_node = create_agent_executor()
workflow.add_node("process_input", process_input_node)
workflow.add_node("agent", agent_node)
workflow.add_node("tool_result", tool_result_node)

# 创建工具节点 - 自动处理工具调用
tool_node = ToolNode(tools)
workflow.add_node("tool", tool_node)

# 设置入口点
workflow.set_entry_point("process_input")

# 添加边
workflow.add_edge("process_input", "agent")
workflow.add_edge("agent", "tool")
workflow.add_edge("tool", "tool_result")
workflow.add_edge("tool_result", "agent")

# 添加条件边
workflow.add_conditional_edges(
    "agent",
    check_completion,
    {
        "agent": "agent",
        "tool": "tool",
        "end": END
    }
)

memory = MemorySaver()
app = workflow.compile(checkpointer=memory, interrupt_before=["tool"])

def run_interactive():
    """
    运行交互式对话
    """
    config = {
        "configurable": {
            "thread_id": str(datetime.now().timestamp())
        }
    }
    
    # 初始化带检查点的状态
    state = {
        "messages": [],
        "collected_params": [],
        "user_input": ""
    }
    
    print("航班助手已启动，输入'退出'结束对话")
    
    while True:
        # 获取用户输入
        user_input = input("用户: ")
        
        if user_input.lower() in ["退出", "exit", "quit", "q"]:
            print("对话结束")
            break
        
        # 更新状态
        state["user_input"] = user_input
        state["messages"].append(HumanMessage(content=user_input))
        loop_graph_invoke(app, user_input, config)
        snapshot_state = app.get_state(config)
        log.debug("snapshot_state= {}", snapshot_state)

        # 获取messages中的最后一条消息
        if snapshot_state.values.get("messages"):
            last_message = snapshot_state.values.get("messages")[-1]
            
            # 检查是否是AIMessage并且需要工具调用
            if not isinstance(last_message, AIMessage) or not hasattr(last_message, "additional_kwargs") :
                continue
            tool_calls = last_message.additional_kwargs.get("tool_calls")
            if tool_calls:
                loop_graph_invoke_tools(app, None, config)

if __name__ == "__main__":
    # 运行交互式对话
    run_interactive()
