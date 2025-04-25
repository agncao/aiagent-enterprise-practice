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
from agent.utils.langgraph_utils import loop_graph_invoke_tools,loop_graph_invoke,draw_graph
from pydantic import BaseModel
from agent.space.space_types import SpaceState, ScenarioConfig, EntityConfig, ToolResult
from agent.space.agent_tool import UserConfirm, continue_workflow_with_tool_result
from agent.space.space_read_tool import read_tools
from agent.space.space_write_tool import write_tools

# 初始化内存检查点
memory = MemorySaver()


@tool
class UserConfirm(BaseModel):
    """
    是否需要用户确认信息
    """
    request: str


# @tool
# def confirm_user_action(action_description: str, details: Dict[str, Any]) -> Dict[str, Any]:
#     """
#     在执行创建或修改操作前，调用此工具向用户确认信息。

#     Args:
#         action_description (str): 需要确认的操作描述 (例如 "创建以下场景", "添加以下实体")。
#         details (Dict[str, Any]): 需要用户确认的具体信息。

#     Returns:
#         Dict[str, Any]: 一个包含确认请求的消息，引导用户确认。
#     """
#     log.info(f"请求用户确认操作: {action_description}, 细节: {details}")
#     details_str = "\n".join([f"- {k}: {v}" for k, v in details.items() if v is not None])
#     prompt = f"请确认是否要{action_description}：\n{details_str}\n请输入 '是' 或 '否'。"
#     # 同样，这个工具生成一个需要AI回复给用户的提示
#     return {"prompt_to_user": prompt}

# --- Agent Node ---
def create_space_agent_executor():
    """创建空间场景 Agent 的执行器节点"""

    space_tools = read_tools + write_tools
    prompt = ChatPromptTemplate.from_messages([
        ("system", """你是一个智能空间态势助手。你的任务是与用户交互，理解他们的意图（例如查询场景、创建场景、添加卫星/地面站），收集必要的信息，确认信息，然后调用相应的工具来执行操作。

        当前时间: {time}
        工作流程:
        1.  问候用户，理解他们的请求意图 (intent)。
        2.  如果意图是查询场景或实体（如包含‘查询’、‘是否存在’等关键词）：
            a. 解析用户输入，提取查询对象信息。
            b. 优先调用相关查询工具（如 query_scenario_exists、query_scenario_entities），并将结果反馈给用户。
        3.  如果意图是创建场景或添加实体：
            a. 解析用户输入，提取必要的信息。
            b. 检查信息是否完整。如果不完整，则请求用户提供缺失的信息。
            c. 如果信息完整，则请求用户确认。
            d. 天体中心需要解析成英文，比如："地球" -> "Earth"; "月球" -> "Moon"; "火星" -> "Mars" 等。
        4.  如果用户的回复是确认信息（例如 '是', '确认'），表示收集的信息正确，执行操作。
        5.  如果用户的回复是否认信息（例如 '否', '取消'），表示用户的意图理解的不正确，请求用户更正。
        6.  工具执行完成，无论执行成功与否，都回复给用户。
        
        注意:
        - 由于实体是属于场景的一部分，所以添加实体前先添加或者查询某个场景。
        - 请根据用户输入的关键词（如“查询”、“是否存在”、“获取”等）优先判断是否为查询类意图，并自动调用相关查询工具。
        
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
        temperature=0, # 对于需要精确遵循指令的任务，温度设低一些
        streaming=True
    )
    llm_with_tools = llm.bind_tools(tools=space_tools+[UserConfirm])
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

        new_state_update = {"messages": [response]}
        tool_calls = response.additional_kwargs.get("tool_calls", [])

        if tool_calls:
            log.info(f"agent_node请求调用工具: {[call['function']['name'] for call in tool_calls]}")
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
    """
    处理工具的输出，更新状态
    """
    log.debug(f"--- Routing After Tools --- State: {state}")
    # 工具执行后，总是返回 Agent 进行下一步处理
    # Agent 会根据工具结果和当前状态决定是回复用户、请求确认、收集更多信息还是结束

    state.pop("action", None)
    state.pop("tool_func", None)
    state.pop("tool_func_args", None)
    state["completed"] = True

    last_message = state["messages"][-1]
    if not isinstance(last_message, ToolMessage):
        return state

    tool_name = getattr(last_message, 'name', None)
    agent_tools = ["UserConfirm"]
    if tool_name in agent_tools:
        pass
    else:
        try:
            tool_result_json = json.loads(last_message.content)
            last_message.content = tool_result_json.get("message", "")
            state["tool_result"] = tool_result_json
        except Exception as e:
            log.error(f"工具结果解析失败: {e}")
            raise e
    return state

# --- Graph Definition ---
workflow = StateGraph(SpaceState)

# 添加节点
agent_executor_node = create_space_agent_executor()
workflow.add_node("agent", agent_executor_node)
workflow.add_node("tools", ToolNode(read_tools+write_tools))
workflow.add_node("process", process_tools_output)
workflow.add_node("continue_tool", continue_workflow_with_tool_result) 

# 设置入口点
workflow.set_entry_point("agent")

# 定义边的逻辑
def route_after_agent(state: SpaceState):
    """决定 Agent 执行后的下一个节点"""
    if state.get("completed", False):
        log.info("Tool execution completed. Ending turn.")
        return END
    
    if state.get("action") == "tool_call" and state.get("tool_func"):
        if state["tool_func"].startswith("query_"):
            log.info(f"工具 {state['tool_func']}执行中断, 等待平台响应....")
            return "continue_tool"  
        log.info(f"工具 {state['tool_func']} 执行中...")
        return "tools"
    else:
        log.info("No tool call requested. Ending turn.")
        return END 

# 添加边
workflow.add_conditional_edges(
    "agent",
    route_after_agent,
    {
        "tools": "tools",
        "continue_tool": "continue_tool",
        END: END
    }
)
workflow.add_edge("tools", "process")
workflow.add_edge("process", "agent")
# continue_tool 节点恢复后回到 agent
workflow.add_edge("continue_tool", "agent")

# 编译 Graph
app = workflow.compile(checkpointer=memory, interrupt_before=["continue_tool"])

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
