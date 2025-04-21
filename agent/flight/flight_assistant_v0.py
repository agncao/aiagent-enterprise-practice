from datetime import datetime
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langgraph.prebuilt.tool_node import tools_condition
from langchain_core.runnables import RunnablePassthrough
from langgraph.prebuilt import ToolNode
from infrastructure.config import config
from agent.utils.langgraph_utils import loop_graph_invoke_tools,loop_graph_invoke,draw_graph
from infrastructure.logger import log
from agent.utils.base_state import BaseState
from service.flight_service import FlightParams,search_flights
from pydantic import BaseModel, Field

# 初始化内存检查点（带自动清理）
memory = MemorySaver()  # 每100次操作清理一次旧数据

@tool(args_schema = FlightParams)
def check_params(departure_airport, arrival_airport, departure_time):
    """
    检查参数是否正确
    
    Args:
        departure_airport (str): 出发城市
        arrival_airport (str): 到达城市
        departure_time (str): 出发日期
        
    Returns: dict 验证结果
    """

    log.debug("check_params 收集到的参数: 出发城市:{},抵达城市:{},出发日期:{}", departure_airport, arrival_airport, departure_time)

    return {"success": True,"message":"参数验证通过，准备查询航班"}

class UserAction(BaseModel):
    input: str

@tool
def user_action_node(state:BaseState):
    """
    是否需要用户输入
    - state["user_action"]为True时，表示需要用户手动输入
    - state["user_action"]为False时，表示不需要用户手动输入
    
    Args:
        state (BaseState): 当前状态
    
    Returns:
        dict: 包含user_action字段
    """
    return {"messages": [],"user_action": False}

tools = [check_params, search_flights]

# ---------------------------
# 3. 构建带检查点的工作流
# ---------------------------
def create_agent_executor():
    """
    代理节点，处理用户输入，调用LLM生成回复
    
    Args:
        state (BaseState): 当前状态
    
    Returns:
    """
    
    # 提示模板
    prompt = ChatPromptTemplate.from_messages([
        ("system", """你是一个航班助手，可以帮助用户查询航班信息。
        
        你可以收集用户的航班需求，包括出发地、目的地和出发日期，然后使用工具来查询航班信息。
        
        工作流程：
        1. 收集用户的航班需求（出发地、目的地、出发日期）
        2. 使用 check_params 工具检查参数是否完整
        3. 必须先使用 check_params 验证参数符合规范后，再调用 search_flights 工具
        4. 向用户展示搜索结果

        重要提示：当前时间是{time}。
        """),
        MessagesPlaceholder(variable_name="history_messages"),
        ("human", "{user_input}"),
    ]).partial(time=datetime.now())
    
    llm = ChatOpenAI(
        base_url=config.get("llm.base_url"),
        api_key=config.get("llm.api_key"),
        model_name=config.get("llm.model_name"),
        streaming=True
    )
    llm_with_tools = llm.bind_tools(tools=tools+[UserAction], tool_choice="auto")
    def agent_node(state: BaseState):
        try:
            chain = RunnablePassthrough.assign(
                history_messages=lambda x: state["messages"],
            ) | prompt | llm_with_tools
            outs = chain.invoke(state)
            log.debug("LLM响应: {}", outs)
            res = {"messages": [outs], "user_input": state["user_input"], "action": None, "tool_call_name": None,"user_action": False}

            if isinstance(outs, AIMessage) and hasattr(outs, "additional_kwargs") and outs.additional_kwargs.get("tool_calls"):
                tool_call = outs.additional_kwargs.get("tool_calls")[0]
                tool_call_name = tool_call.get("function")["name"] if "function" in tool_call else tool_call["name"]
                res = {**res,"user_input":"","action": "tool_call","tool_call_name": tool_call_name}
            
            if res["action"] == "tool_call" and res["tool_call_name"]==UserAction.__name__:
                res["user_action"] = True

            log.debug("agent_node returns: {}", res)
            return res
        except Exception as e:
            log.error("代理执行出错: {}", str(e))
            raise e

    return agent_node

def select_next_node(state: BaseState):
    if state["user_action"]:
        return "user_node"
    # Otherwise, we can route as before
    return tools_condition(state)

# 构建工作流
workflow = StateGraph(BaseState)

# 添加节点
agent_node = create_agent_executor()
workflow.add_node("agent", agent_node)
workflow.add_node("tools", ToolNode(tools))
workflow.add_node("user_node", ToolNode([user_action_node]))

workflow.set_entry_point("agent")
workflow.add_edge("user_node", "agent")

workflow.add_conditional_edges(
    "agent",
    select_next_node,
    {
        "tools": "tools",
        "user_node": "user_node",
        END: END
    }
)
workflow.add_edge("tools", "agent")

memory = MemorySaver()
app = workflow.compile(checkpointer=memory, interrupt_before=["user_node"])

# 新增：导出 Mermaid 源文件
with open("workflow.mmd", "w", encoding="utf-8") as f:
    # 尝试打印所有方法名，找找有没有类似 mermaid 的导出方法
    # print(dir(app.get_graph()))
    f.write(app.get_graph().draw_mermaid())  # 暂时注释掉
# draw_graph(app, "workflow.png")

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
        state["thread_id"] = config["configurable"]["thread_id"]
        loop_graph_invoke(app, user_input, config)
        snapshot_state = app.get_state(config)
        # 获取messages中的最后一条消息
        if snapshot_state.values.get("messages"): 
            last_message = snapshot_state.values.get("messages")[-1]
            
            # 检查是否是AIMessage并且需要工具调用
            if not isinstance(last_message, AIMessage) or not hasattr(last_message, "additional_kwargs") :
                continue
            tool_calls = last_message.additional_kwargs.get("tool_calls")
            if tool_calls:
                loop_graph_invoke_tools(app, config)

if __name__ == "__main__":
    # 运行交互式对话
    run_interactive()
