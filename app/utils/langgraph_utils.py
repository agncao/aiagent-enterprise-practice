from app.utils.base_state import BaseState
from langchain_core.messages import HumanMessage, AIMessage

def draw_graph(graph, png_file):
    try:
        # 生成 graph的图
        image = graph.get_graph().draw_mermaid_png()
        with open(png_file, 'wb') as f:
            f.write(image)
    except Exception as e:
        print(e)


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
            if isinstance(last_message, AIMessage):
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
        events = graph.stream(None, config, stream_mode="values")
        for event in events:
            if "messages" in event and len(event["messages"]) > 0:
                last_message = event["messages"][-1]
                if isinstance(last_message, AIMessage):
                    last_message.pretty_print()


def get_answer(tools_script_message):
    """
    处理工具调用消息，返回工具执行结果
    
    Args:
        tools_script_message: 包含工具调用的消息
    """
    # 这里可以添加处理工具调用的逻辑
    print("\n处理工具调用:", tools_script_message.tool_calls)
    return "工具执行完成"
