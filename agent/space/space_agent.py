import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, BaseMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langgraph.prebuilt import ToolNode, tools_condition
from pydantic import ValidationError
from langchain_core.tools import tool
from infrastructure.config import config
from infrastructure.logger import log
from agent.space.space_types import SpaceState, ConversationState, ScenarioConfig, EntityConfig, ToolResult
from agent.space.space_tools import space_tools
from app.utils.langgraph_utils import loop_graph_invoke_tools,loop_graph_invoke,draw_graph
from pydantic import BaseModel

# 初始化内存检查点
memory = MemorySaver()


@tool
class UserConfirm(BaseModel):
    """
    是否需要用户确认信息
    """
    request: str

# --- Agent Node ---
def create_space_agent_executor():
    """创建空间场景 Agent 的执行器节点"""
    prompt = ChatPromptTemplate.from_messages([
        ("system", """你是一个智能空间态势助手。你的任务是与用户交互，理解他们的意图（例如创建场景、添加卫星/地面站），收集必要的信息，确认信息，然后调用相应的工具来执行操作。

        当前时间: {time}

        工作流程:
        1.  问候用户，理解他们的请求意图 (intent)。
        2.  如果意图是创建场景或添加实体：
            a. 解析用户输入，提取必要的信息。
            b. 检查信息是否完整。如果不完整，则请求用户提供缺失的信息。
            c. 如果信息完整，则请求用户确认。
        3.  如果用户的回复是确认信息（例如 '是', '确认'），表示收集的信息正确，执行操作。
        4.  如果用户的回复是否认信息（例如 '否', '取消'），表示用户的意图理解的不正确，请求用户更正。
        5.  如果意图是执行其他操作（如 `calculate_sgp4`），直接调用相应工具。
        6.  工具执行完成，无论执行成功与否，都回复给用户。

        注意:
        - 由于实体是属于场景的一部分，所以添加实体前先添加或者查询某个场景。
        可用工具: {tool_names}
        """),
        MessagesPlaceholder(variable_name="history_messages"),
        ("human", "{user_input}"),
    ]).partial(
        time=datetime.now,
        tool_names=", ".join([t.name for t in space_tools])
    )

    llm = ChatOpenAI(
        base_url=config.get("llm.base_url"),
        api_key=config.get("llm.api_key"),
        model_name=config.get("llm.model_name"),
        temperature=0, # 对于需要精确遵循指令的任务，温度设低一些
        streaming=True
    )
    llm_with_tools = llm.bind_tools(tools=space_tools)
    def agent_node(state: SpaceState):
        log.debug("--- Agent Node Start ---\n","Current State: ", state)
        history_messages = state.get('messages', [])
        chain = RunnablePassthrough.assign(
            history_messages=lambda x: history_messages,
        ) | prompt | llm_with_tools

        # 调用 LLM
        try:
            response = chain.invoke({"user_input": state["user_input"]})
            log.debug(f"LLM Raw Response: {response}")
        except Exception as e:
            log.error(f"LLM 调用失败: {e}")
            # 可以返回错误状态或默认消息
            error_message = AIMessage(content="抱歉，处理您的请求时遇到问题。")
            return {"messages": [error_message], "conversation_state": ConversationState.ERROR}

        # --- 状态更新逻辑 ---
        new_state_update = {"messages": [response]}

        # 检查 LLM 是否要求调用工具
        tool_calls = response.additional_kwargs.get("tool_calls", [])

        if tool_calls:
            log.info(f"LLM 请求调用工具: {[call['function']['name'] for call in tool_calls]}")
            # 提取第一个工具调用的信息 (LangGraph 通常按顺序处理)
            tool_call = tool_calls[0]
            tool_name = tool_call['function']['name']
            tool_args = json.loads(tool_call['function']['arguments'])
    
            # 传递给 ToolNode
            new_state_update["action"] = "tool_call"
            new_state_update["user_input"] = ""
            new_state_update["tool_func"] = tool_name
            new_state_update["tool_func_args"] = tool_args

        log.debug(f"--- Agent Node End --- Update: {new_state_update}")
        return new_state_update

    return agent_node

# --- Tool Node ---
def process_tools_output(state: SpaceState):
    """决定工具执行后的下一个节点"""
    log.debug(f"--- Routing After Tools --- State: {state}")
    # 工具执行后，总是返回 Agent 进行下一步处理
    # Agent 会根据工具结果和当前状态决定是回复用户、请求确认、收集更多信息还是结束
    state.pop("action", None)
    state.pop("tool_func", None)
    state.pop("tool_func_args", None)
    state["completed"] = True

    return state


# --- Graph Definition ---
workflow = StateGraph(SpaceState)

# 添加节点
agent_executor_node = create_space_agent_executor()
workflow.add_node("agent", agent_executor_node)
workflow.add_node("tools", ToolNode(space_tools))
workflow.add_node("process", process_tools_output)

# 设置入口点
workflow.set_entry_point("agent")

# 定义边的逻辑
def route_after_agent(state: SpaceState):
    """决定 Agent 执行后的下一个节点"""
    log.debug(f"--- Routing Decision --- State: {state}")
    
    # 如果状态标记为已完成，结束当前轮次
    if state.get("completed", False):
        log.info("Tool execution completed. Ending turn.")
        return END
    
    # 如果有工具调用请求，路由到工具节点
    if state.get("action") == "tool_call" and state.get("tool_func"):
        return "tools"
    else:
        # 如果没有工具调用，对话结束或等待用户下一次输入
        log.info("No tool call requested. Ending turn.")
        return END # 或者可以路由回 agent 等待下一次用户输入

# 添加边
workflow.add_conditional_edges(
    "agent",
    route_after_agent,
    {
        "tools": "tools",
        END: END
    }
)
workflow.add_edge("tools", "process")
workflow.add_edge("process", "agent")

# 编译 Graph
app = workflow.compile(checkpointer=memory)

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

        final_response = None
        full_response_content = "" # 用于累积助手的完整回复

        events = app.stream(inputs, config, stream_mode="values")
        for event in events:
            if "messages" in event and len(event["messages"]) > 0:
                last_message = event["messages"][-1]
                if isinstance(last_message, AIMessage) and not hasattr(event,"action") and not hasattr(event,"tool_func"):
                    if last_message.content != full_response_content:
                        print(f"助手: {last_message.content[len(full_response_content):]}", end="", flush=True)
                        full_response_content = last_message.content
            final_response = event 

        print() 
        # 图的流程会自动处理工具调用

if __name__ == "__main__":
    run()
