from app.utils.base_state import BaseState
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
import logging
from app.utils.base_state import StateUtils

logger = logging.getLogger(__name__)

def draw_graph(graph, png_file):
    try:
        # 生成 graph的图
        image = graph.get_graph().draw_mermaid_png()
        with open(png_file, 'wb') as f:
            f.write(image)
    except Exception as e:
        logger.error(f"绘制图表出错: {str(e)}")
        raise e


def loop_graph_invoke(graph, user_input: str, config):
    """
    循环调用这个流程图，让AI可以一直和用户对话
    使用 BaseState 格式，确保与 BaseAssistant 兼容
    
    Args:
        graph: 工作流图
        user_input: 用户输入
        config: 配置
    """
    initial_state = BaseState(
        messages=[HumanMessage(content=user_input)],
        user_input=user_input
    )
    
    # stream_mode="values"：这意味着该方法将会直接返回事件中的值，而不是整个事件对象。
    # 这使得处理过程更加简洁，特别是当你只关心事件的具体内容而非其元数据时。
    events = graph.stream(dict(initial_state), config, stream_mode="values")
    for event in events:
        if "messages" in event and len(event["messages"]) > 0:
            last_message = event["messages"][-1]
            if StateUtils.ready_call_tool(event):
                logger.debug(f"Ready to call tool, tool_name: {event['tool_name']}, tool_args: {event['tool_args']}")
            else:
                last_message.pretty_print()


def loop_graph_invoke_tools(graph, user_input: str, config):
    """
    循环调用这个流程图，让AI可以一直和用户对话
    支持工具调用，使用 BaseState 格式
    
    Args:
        graph: 工作流图
        user_input: 用户输入
        config: 配置
    """
    if user_input:
        # 使用 BaseState 格式创建初始状态
        initial_state = BaseState(
            messages=[HumanMessage(content=user_input)],
            user_input=user_input
        )
        
        events = graph.stream(dict(initial_state), config, stream_mode="values")
        for event in events:
            if "messages" in event and len(event["messages"]) > 0:
                last_message = event["messages"][-1]
                if isinstance(last_message, AIMessage):
                    last_message.pretty_print()
    else:
        # 如果没有用户输入，则继续使用当前状态
        tool_result_displayed = False
        events = graph.stream(None, config, stream_mode="values")
        
        for event in events:
            if "messages" in event and len(event["messages"]) > 0:                
                for message in event["messages"]:
                    if isinstance(message, AIMessage):
                        # 显示AIMessage的内容给用户
                        print(f"助理: {message.content}", end="\n")
                        tool_result_displayed = True
        
        # 如果没有显示任何工具结果，提供默认消息
        if not tool_result_displayed:
            print("助理: 我正在处理您的请求...", end="\n")


def get_answer(tools_script_message):
    """
    处理工具调用消息，返回工具执行结果
    
    Args:
        tools_script_message: 包含工具调用的消息
    """
    logger.debug("处理工具调用:", tools_script_message.tool_calls)
    return "工具执行完成"

def parse_output(output):
    """解析LLM输出，识别工具调用"""
    if tool_calls := output.additional_kwargs.get("tool_calls"):
        tool_call = tool_calls[0]
        # 创建一个字典，包含工具调用信息
        return {
            "messages": [AIMessage(
                content=output.content,
                additional_kwargs={"tool_calls": tool_calls})],
            "action": "tool_call",
            "tool_name": tool_call["function"]["name"],
            "tool_args": tool_call["function"]["arguments"]
        }
    return AIMessage(content=output.content)