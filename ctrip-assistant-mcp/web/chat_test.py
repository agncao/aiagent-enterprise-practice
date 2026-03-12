'''
用户gradio生成了 一个聊天界面的测试页面
'''

import uuid
from app.multi_agent.workflow.primary_workflow import build_primary_workflow
from app.multi_agent.workflow.init_db import update_dates
from langchain_core.messages import ToolMessage,AIMessage
from app.multi_agent.workflow.base import print_event
from config import get_logger

logger = get_logger(__name__)

INTERRUPT_NODES = {
    "hotel_write_tools",
    "flight_write_tools",
    "car_rental_write_tools",
    "trip_write_tools",
}


import gradio as gr


def append_chat_history(user_input, chat_history):
    """
    输入框提交后，执行的函数: 将输入添加到聊天记录里
    :param user_input: 用户输入的文本
    :param chat_history: 聊天历史记录列表
    :return: 更新后的用户输入和聊天历史记录
    """

    chat_history.append({"role": "user", "content": user_input})
    # 清空用户输入框
    user_input = ""
    
    return user_input, chat_history

update_dates()
session_id=str(uuid.uuid4())
config = {
    "configurable": {
        # passenger_id用于我们的航班工具，以获取用户的航班信息
        "passenger_id": "3442 587242",
        # 检查点由session_id访问
        "thread_id": session_id,
    }
}

_printed = set()
graph = build_primary_workflow()
def do_workflow(chat_history:list[dict]):
    """
    执行工作流，处理用户输入并返回助手的响应。
    :param chat_history: 聊天历史记录列表
    :return: 更新后的聊天历史记录
    """
    result = ''
    logger.info(f"start to do workflow: {chat_history[-1]}")
    user_input = chat_history[-1]["content"]
    if isinstance(user_input, list) and len(user_input) > 0:
        user_input = user_input[0]["text"]
    logger.info(f"user_input: {user_input}")

    current_state = graph.get_state(config)
    pending_nodes = set(current_state.next or ())
    in_interrupt = bool(pending_nodes & INTERRUPT_NODES)

    if in_interrupt:
        if user_input.strip().lower() == 'y':
            events = graph.stream(None, config, stream_mode='updates')
        else:
            messages = current_state.values.get("messages", [])
            last_tool_calls = []
            for msg in reversed(messages):
                tool_calls = getattr(msg, "tool_calls", None) or []
                if tool_calls:
                    last_tool_calls = tool_calls
                    break
            reject_messages = [
                ToolMessage(
                    tool_call_id=tc["id"],
                    content=f"Tool的调用被用户拒绝。原因：'{user_input}'。",
                )
                for tc in last_tool_calls
            ]
            if reject_messages:
                events = graph.stream({"messages": reject_messages}, config, stream_mode='updates')
            else:
                events = graph.stream({"messages": [("user", user_input)]}, config, stream_mode='updates')
    else:
        events = graph.stream({"messages": [("user", user_input)]}, config, stream_mode='updates')
        
    for event in events:
        print_event(event, _printed)
        message = event.get("messages")
        if not message:
            for node_name, payload in event.items():
                if not isinstance(payload, dict):
                    continue
                if "messages" in payload:
                    message = payload["messages"]
                    if isinstance(message, list):
                        message = message[-1] if message else None

        if message and isinstance(message, AIMessage) and message.content.strip() != '':
            result=message.content

    current_state = graph.get_state(config)
    pending_nodes = set(current_state.next or ())
    if pending_nodes & INTERRUPT_NODES:
        result = "AI助手马上根据你要求，执行相关操作。您是否批准上述操作？输入'y'继续；否则，请说明您请求的更改。\n"

    chat_history.append({"role": "assistant", "content": result})
    return chat_history


css = '''
#bgc {background-color: #7FFFD4}
.feedback textarea {font-size: 24px !important}
'''

with gr.Blocks(title='携程AI智能助手') as instance:
    gr.Label("携程助手测试",container=False)
    
    chatbot = gr.Chatbot(height=500, label="AI助手")
    input_text = gr.Textbox(label="请输入你的问题",value='') #输入文本组件

    input_text.submit(fn=append_chat_history, inputs=[input_text, chatbot], outputs=[input_text, chatbot]).then(
        fn=do_workflow, inputs=[chatbot], outputs=[chatbot]
    )

if __name__ == '__main__':
    # 启动Gradio应用
    instance.launch(css=css)