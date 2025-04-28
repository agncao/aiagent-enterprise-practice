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
from agent.space.space_types import SpaceState, CommandInfo, ToolInfo
from agent.space.agent_tool import confirm_user_action
from agent.space.space_read_tool import query_scenario, read_tools
from agent.space.space_write_tool import write_tools
from agent.space.utils.langgraph_utils import get_tool_info

# 初始化内存检查点
memory = MemorySaver()

# --- Agent Node ---
def create_space_agent_executor():
    """创建空间场景 Agent 的执行器节点"""

    space_tools = read_tools + write_tools
    prompt = ChatPromptTemplate.from_messages([
        ("system", """你是一个专业的空间场景助手，帮助用户创建和管理空间场景、添加实体（如卫星、地面站等）。

        当前时间: {time}
        工作流程:
        1.  问候用户，理解他们的请求意图 (intent)。
        2.  如果意图是创建场景或添加实体（包括卫星、地面站等）：
            a. 解析用户输入，提取必要的信息。
            b. 检查信息是否完整。如果不完整，则请求用户提供缺失的信息。
            c. 如果信息完整，则必须使用confirm_user_action工具请求用户确认，再调用其他工具。
            d. 天体中心需要解析成英文，比如："地球" -> "Earth"; "月球" -> "Moon"; "火星" -> "Mars" 等。
        3.  如果意图是添加实体（包括卫星、地面站等）还需要特别注意：
            a. 确定在此之前，助手已经成功创建了场景。
            b. 如果还没创建场景，则请求用户先创建或者查询所需要的场景
        4.  如果用户的回复是确认信息（例如 '是', '确认'），表示收集的信息正确，执行操作。
        5.  如果用户的回复是否认信息（例如 '否', '取消'），表示用户的意图理解的不正确，请求用户更正。    
    
        重要提示:
        - 添加任何实体前，都必须确保场景存在。
        - 收集完工具所需参数后必须先使用confirm_user_action工具请求用户确认，再进行其他工具的调用
        - 永远不要跳过用户确认步骤，这是强制性的要求

        示例对话:
        用户: "我想创建一个名为'太空任务'的场景，中心天体是地球，时间从2025-01-01到2025-01-02"
        助手: [使用confirm_user_action工具] "请确认是否要创建以下场景：
        - name: 太空任务
        - centralBody: Earth
        - startTime: 2025-01-01T00:00:00.000Z
        - endTime: 2025-01-02T00:00:00.000Z
        请输入 '是' 或 '否'。"
        用户: "是"
        助手: [使用create_scenario工具] "场景'太空任务'已成功创建！"

        用户: "添加一颗卫星，TLE是[...]"
        助手: [使用confirm_user_action工具] "请确认是否要添加以下卫星：
        - TLEs: [...]
        请输入 '是' 或 '否'。"
        用户: "是"
        助手: [使用add_satellite_entity工具] "卫星已成功添加到场景中。"

        可用工具: {tool_names}\n"""),
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
        temperature=0.1, # 对于需要精确遵循指令的任务，温度设低一些
        streaming=True
    )
    llm_with_tools = llm.bind_tools(tools=space_tools+[confirm_user_action])
    def agent_node(state: SpaceState):
        log.debug("===========Agent Node Start============ \nState: ", state)
        history_messages = state.get('messages', [])
        chain = RunnablePassthrough.assign(
            history_messages=lambda x: history_messages,
        ) | prompt | llm_with_tools

        # 调用 LLM
        try:
            response = chain.invoke({"user_input": state["user_input"]})
            log.debug(f"agent_node Response: {response}")
        except Exception as e:
            log.error(f"agent_node error: {e}")
            return {"messages": [AIMessage(content="抱歉，处理您的请求时遇到问题。")]}

        new_state_update = {"messages": [response],"user_input":""}
        tool_info = get_tool_info(response)
        if tool_info and tool_info.name != "confirm_user_action":
            new_state_update["tool_info"] = ToolInfo.model_validate(tool_info)
        log.debug(f"--- Agent Node End --- Update: {new_state_update}")
        return new_state_update

    return agent_node

# --- Tool Node ---
def process_tools_output(state: SpaceState):
    """
    处理工具执行结果，生成 AI 回复
    
    Args:
        state: 当前状态
    
    Returns:
        更新后的状态
    """
    tool_result_external = state.get("tool_result")
    if tool_result_external:
        log.info(f"process_tools_output: external result: {tool_result_external}")
        if tool_result_external.get("tool_func").startswith("query_"):
            data = tool_result_external.get("data",[])
            update_state = {"messages": [AIMessage(content=f"{tool_result_external['message']}\n{data}")],"completed": True}
        else:
            update_state = {"messages": [AIMessage(content=tool_result_external["message"])],"completed": True}
        if "has_answered" in state: 
            update_state["has_answered"] = True
        log.debug(f"process_tools_output: Thread ID: {state.get('thread_id')},update state: {update_state}")
        return update_state
    
    return {}

# --- Graph Definition ---
workflow = StateGraph(SpaceState)

# 添加节点
agent_executor_node = create_space_agent_executor()
workflow.add_node("agent", agent_executor_node)
workflow.add_node("tools", ToolNode(read_tools+write_tools))
workflow.add_node("confirm", ToolNode([confirm_user_action]))
workflow.add_node("process", process_tools_output)

# 设置入口点
workflow.set_entry_point("agent")

# 定义边的逻辑
def route_after_agent(state: SpaceState):
    """决定 Agent 执行后的下一个节点"""
    if state.get("completed") or len(state["messages"]) == 0:
        return END
    last_message = state["messages"][-1]
    tool_info = get_tool_info(last_message)
    if isinstance(last_message, AIMessage) and tool_info:
        if tool_info.name != "confirm_user_action":
            return "tools"
        return "confirm"

    log.info("No tool call requested. Ending turn.")
    return END

# 添加边
workflow.add_conditional_edges(
    "agent",
    route_after_agent,
    {
        "tools": "tools",
        "confirm": "confirm",
        END: END
    }
)

workflow.add_edge("tools", "process")
workflow.add_edge("process","agent")
workflow.add_edge("confirm","agent")

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
