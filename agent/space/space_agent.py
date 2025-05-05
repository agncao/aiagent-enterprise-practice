import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, BaseMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langgraph.prebuilt import ToolNode
from infrastructure.config import config
from infrastructure.logger import log
from agent.space.space_types import SpaceState, Operation, CommandType
from agent.space.space_read_tool import read_tools
from agent.space.space_write_tool import write_tools
from agent.space.utils.langgraph_utils import get_tool_info,valid_tool_call

# 初始化内存检查点
memory = MemorySaver()

# --- Agent Node ---
def create_space_agent_executor():
    """创建空间场景Agent的执行器节点"""

    all_tools = read_tools + write_tools
    prompt = ChatPromptTemplate.from_messages([
        ("system", """你是一个无所不能的航空航天智能分析系统的助手。
        
        1. 你的职责是识别用户意图，帮助用户管理场景和实体信息等，例如：查看全部实体、添加地面车、修改场景名等。
        2. 当用户只输入了一个航天航空专业名词时(例如：场景、地面站)，可尝试请求创建场景、添加地面站。
        3. 重要：当请求执行某个操作时(例如：查看全部实体、添加地面车、修改场景名等)，即便没有提供任何参数自身提供的默认值立即调用对应的工具。对于未提供的参数：
           - 如果参数是可选的（Optional），则传递None值
           - 不要自己生成或猜测参数值，除非用户明确提供
           - 更不要询问用户提供默认参数
        4. 天体中心需要解析成英文，比如："地球" -> "Earth"; "月球" -> "Moon"; "火星" -> "Mars" 等。
        5. 在生成工具调用参数时，必须使用严格的 JSON 格式。
        6. 工具会在中断处获得外部系统给出的执行结果，你需要用简洁的概括性语言来描述执行结果，并列举出所执行的参数(如果工具入参不为空的话)。
        7. 查询类的工具会有返回结果，需要你一一列出返回值。如果没有返回值，请提示用户。

        重要提示：
        1. 当用户请求执行某个操作时，即使用户没有提供所有参数，也立即使用对应的工具。不要询问用户是否要使用默认值，直接执行。
        2. 语言要自然简洁


        当前时间: {time}。
        可用的读工具: {read_tools_names}。
        可用的写工具: {write_tools_names}。
        """),
        MessagesPlaceholder(variable_name="history_messages"),
        ("human", "{user_input}"),
    ]).partial(
        time=datetime.now,
        read_tools_names=", ".join([t.name for t in read_tools]),
        write_tools_names=", ".join([t.name for t in write_tools])
    )

    llm = ChatOpenAI(
        base_url=config.get("llm.base_url"),
        api_key=config.get("llm.api_key"),
        model_name=config.get("llm.model_name"),
        temperature=0.1, # 对于需要精确遵循指令的任务，温度设低一些
        streaming=True
    )
    llm_with_tools = llm.bind_tools(tools=all_tools)
    def agent_node(state: SpaceState):
        log.debug(f"===========Agent Node Start============ \nState: {state}")
        history_messages = state.get('messages', [])
        chain = RunnablePassthrough.assign(
            history_messages=lambda x: history_messages,
        ) | prompt | llm_with_tools
        
        if "user_input" in state and state["user_input"]:
            # 重置 completed 标志，确保新的用户输入可以被处理
            update_state = {"completed": False}
            
            try:
                response = chain.invoke({"user_input": state["user_input"]})
                log.debug(f"agent_node Response: {response}")
                if isinstance(response, AIMessage):
                    valid_tool_call(response)
                
                new_state_update = {"messages": [response], "user_input": None}
                return new_state_update
            except Exception as e:
                log.error(f"agent_node error: {e}")
                return {"messages": [AIMessage(content="抱歉，处理您的请求时遇到问题。")], "completed": True}
        
        return {}

    return agent_node

def process_tools_output(state: SpaceState):
    """处理工具执行结果
    
    Args:
        state: 当前状态
    
    Returns:
        更新后的状态
    """
    log.debug("========process_tools_output===========")
    tool_call_response = state.get("tool_call_response")
    if tool_call_response:
        log.info(f"process_tools_output: external result: {tool_call_response}")
        
        # 获取工具名称和参数，用于更自然的语言描述
        tool_func = tool_call_response.get("tool_func", "")
        args = tool_call_response.get("args", {})
        success = tool_call_response.get("success", False)
        message = tool_call_response.get("message", "")
        
        # 展示参数信息
        call_info=""
        if args and any(args.values()):
            args_str = "\n- ".join([f"{k} = {v}" for k, v in args.items() if v is not None])
            call_info = f"参数：\n- {args_str}"

        if success:
            # 查询类工具，会有返回结果
            if tool_func in [getattr(tool, "name", None) for tool in read_tools]:
                message = "没有查询到相关数据"
                if tool_call_response.get("data", []):
                    data_str = "\n".join([f"- {item}" for item in tool_call_response.get("data", [])])
                    call_info = f"{call_info}，查询结果：\n{data_str}"
        content = f"{message}，{call_info}"
        
        ai_message = AIMessage(content=content)
        
        update_state = {
            "messages": [ai_message], 
            "completed": True,
            "tool_info":None,
            "tool_call_response":None
        }
        
        log.debug(f"process_tools_output: update state: {update_state}")
        return update_state
    
    return {}

# --- Graph Definition ---
workflow = StateGraph(SpaceState)

# 添加节点
agent_executor_node = create_space_agent_executor()
workflow.add_node("agent", agent_executor_node)
workflow.add_node("read_tools", ToolNode(read_tools))
workflow.add_node("write_tools", ToolNode(write_tools))
workflow.add_node("process", process_tools_output)


# 设置入口点
workflow.set_entry_point("agent")

# 定义边的逻辑
def route_after_agent(state: SpaceState):
    """决定 Agent 执行后的下一个节点"""
    if state.get("completed") or len(state["messages"]) == 0:
        log.debug("State completed or no messages, ending turn.")
        return END
    
    last_message = state["messages"][-1]
    tool_info = get_tool_info(last_message)
    log.debug(f"Tool info from message: {tool_info}")
    
    if isinstance(last_message, AIMessage) and tool_info:
        if tool_info['name'] in [t.name for t in read_tools]:
            log.debug(f"Routing to read_tools for tool: {tool_info['name']}")
            return "read_tools"
        elif tool_info['name'] in [t.name for t in write_tools]:
            log.debug(f"Routing to write_tools for tool: {tool_info['name']}")
            return "write_tools"
    
    log.info("No tool call requested. Ending turn.")
    return END

# 添加边
workflow.add_conditional_edges(
    "agent",
    route_after_agent,
    {
        "read_tools": "read_tools",
        "write_tools": "write_tools",
        END: END
    }
)

workflow.add_edge("read_tools", "process")
workflow.add_edge("write_tools", "process")
workflow.add_edge("process", "agent")

# 编译 Graph
app = workflow.compile(checkpointer=memory, interrupt_before=["process"])

# draw_graph(app,"space_agent_graph")

# --- 运行交互式对话 (示例) ---
def run():
    """运行空间 Agent 的交互式对话"""
    thread_id = f"space-thread-{datetime.now().timestamp()}"
    config = {"configurable": {"thread_id": thread_id}}
    print(f"Space Agent 已启动 (Thread ID: {thread_id})。输入 '退出' 结束对话。")

    while True:
        user_input = input("用户: ")
        if user_input.lower() in ["退出", "exit", "quit", "q"]:
            print("对话结束。")
            break

        inputs = {
            "messages": [HumanMessage(content=user_input)], # 只传递当前用户输入作为新消息
            "user_input": user_input,
            "completed": False
        }

        full_response_content = "" # 用于累积助手的完整回复

        events = app.stream(inputs, config, stream_mode="values")
        for event in events:
            if "messages" in event and len(event["messages"]) > 0:
                last_message = event["messages"][-1]
                tool_info = get_tool_info(last_message)
                if isinstance(last_message, AIMessage) and tool_info:
                    if last_message.content != full_response_content:
                        print(f"助手: {last_message.content[len(full_response_content):]}", end="", flush=True)
                        full_response_content = last_message.content
            final_response = event 

        print() 
        # 图的流程会自动处理工具调用

if __name__ == "__main__":
    run()
