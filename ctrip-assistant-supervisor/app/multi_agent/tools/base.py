"""工具基类和工具创建辅助函数"""
from langchain_core.messages import ToolMessage
from langchain_core.runnables import RunnableLambda
from langgraph.prebuilt import ToolNode


def handle_tool_error(state) -> dict:
    """
    处理工具调用时发生的错误。

    参数:
        state (dict): 当前的状态字典，包含错误信息和消息列表。

    返回:
        dict: 包含错误信息的新消息列表的字典。
    """
    error = state.get("error")  # 获取错误信息
    tool_calls = state["messages"][-1].tool_calls  # 获取最后一条消息中的所有工具调用
    return {
        "messages": [
            ToolMessage(
                content=f"错误: {repr(error)}\n请修正您的错误。",
                tool_call_id=tc["id"],  # 关联到发生错误的工具调用ID
            )
            for tc in tool_calls  # 遍历所有的工具调用并生成对应的消息
        ]
    }

def create_tool_node_with_fallback(tools: list) -> dict:
    """
    创建一个带有回退机制的工具节点。当指定的工具执行失败时（例如抛出异常），将触发回退操作。

    参数:
        tools (list): 工具列表。

    返回:
        dict: 带有回退机制的工具节点。
    """
    return ToolNode(tools).with_fallbacks(
        # 这里是给 ToolNode 加了一个回退处理：当工具执行过程中抛出异常时，会走 with_fallbacks ，
        # 并把异常写到状态里的 error ，
        # 然后由 RunnableLambda(handle_tool_error) 来生成一条 ToolMessage 作为错误响应
        [RunnableLambda(handle_tool_error)], exception_key="error"
    )
