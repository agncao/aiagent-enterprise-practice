"""
WebSocket 辅助模块，用于处理 LangGraph 应用与 WebSocket 之间的通信。
提供消息处理、去重和错误处理功能。
"""
import json
import hashlib
from typing import Dict, Any, Set
from fastapi import WebSocket
from langchain_core.messages import AIMessage, ToolMessage, HumanMessage
from langgraph.prebuilt.chat_agent_executor import AgentState
from infrastructure.logger import log
from agent.space.space_agent import app
from agent.space.utils.langgraph_utils import get_tool_info

class WebSocketMessageHandler:
    """WebSocket 消息处理器，用于处理 LangGraph 应用与 WebSocket 之间的通信"""
    
    def __init__(self, websocket: WebSocket, app: Any):
        """
        初始化 WebSocket 消息处理器
        
        Args:
            websocket: FastAPI WebSocket 连接
            app: LangGraph 应用实例
        """
        self.websocket = websocket
        self.app = app
        self.cached_messages: Set[str] = set()  # 用于消息去重
    
    def _generate_message_key(self, msg_type: str, content: Any) -> str:
        """生成消息唯一键，用于去重"""

        content_str = json.dumps(content) if isinstance(content, dict) else str(content)
        content_hash = hashlib.md5(content_str.encode()).hexdigest()
        return f"{msg_type}:{content_hash}"
    
    async def send_message(self, msg_type: str, content: Any, thread_id: str) -> bool:
        """
        发送消息到 WebSocket 客户端，带有去重机制
        
        Args:
            msg_type: 消息类型
            content: 消息内容
            thread_id: 会话 ID
            
        Returns:
            bool: 消息是否已发送（如果是重复消息则返回 False）
        """
        message_key = self._generate_message_key(msg_type, content)
        
        # 检查是否是重复消息
        if message_key in self.cached_messages:
            log.debug(f"跳过了重复消息: {msg_type} - {content}")
            return False
        
        # 发送消息
        message = {
            "type": msg_type,
            "thread_id": thread_id
        }
        
        # 根据消息类型添加不同的内容
        if msg_type == "ai_message":
            message["content"] = content
        elif msg_type == "tool_call":
            message["tool_func"] = content.get("tool_func")
            message["tool_func_args"] = content.get("tool_func_args")
        elif msg_type == "error":
            message["message"] = content
        elif msg_type == "end":
            pass  # 结束消息不需要额外内容
        else:
            # 对于其他类型的消息，直接添加内容
            message.update(content if isinstance(content, dict) else {"content": content})
        
        await self.websocket.send_json(message)
        log.debug(f"发送消息: {message}, key: {message_key}")
        if msg_type != "tool_call":
            self.cached_messages.add(message_key)
        return True
    
    async def process_event_stream(self, thread_id: str, user_input: str=None) -> None:
        """
        处理 LangGraph 事件流，并发送相应消息到 WebSocket 客户端
        
        Args:
            user_input: 用户输入
            thread_id: 会话 ID
        """
        config_invoke = {"configurable": {"thread_id": thread_id}}
        if user_input :
            initial_state =AgentState(
                messages=[HumanMessage(content=user_input)],
                user_input=user_input,
                completed=False
            )
            self.cached_messages.clear()
            events_stream = self.app.stream(initial_state, config_invoke, stream_mode="values")
        else:
            events_stream = self.app.stream(None, config_invoke, stream_mode="values")
        for event in events_stream:
            # 处理消息
            if "messages" in event and len(event["messages"]) > 0:
                last_message = event["messages"][-1]
                tool_info = get_tool_info(last_message)
                try:
                    if isinstance(last_message, AIMessage) and last_message.content:
                        await self.send_message("ai_message", last_message.content, thread_id)
                    # 处理工具调用
                    elif isinstance(last_message, ToolMessage) :
                        try:
                            if isinstance(last_message.content, str):
                                tool_info = json.loads(last_message.content)
                            else:
                                tool_info = last_message.content
                
                            if tool_info and not event.get("tool_call_response"):
                                tool_data = {
                                    "tool_func": tool_info.get("func"),
                                    "tool_func_args": tool_info.get("args",None)
                                }
                                await self.send_message("tool_call", tool_data, thread_id)
                        except Exception as e:
                            log.error(f"工具调用处理错误: {e}")
                            raise e
                except Exception as e:
                    log.error(f"事件流处理错误: {e}")
                    raise e
        # 发送结束消息
        await self.send_message("end", None, thread_id)

                
    
    async def handle_tool_result(self, data: Dict[str, Any]) -> None:
        """
        处理工具执行结果
        
        Args:
            data: 包含工具执行结果的数据
        """
        log.info(f"收到工具执行结果: {data}")
        try:
            config_invoke = {"configurable": {"thread_id": data["thread_id"]}}
            self.app.update_state(config_invoke, 
            {
                "tool_call_response": data
            })
            await self.process_event_stream(data["thread_id"],None)   #需要回到中断处
        except Exception as e:
            log.error(f"工具结果处理错误: {e}")
            await self.send_message("error", str(e), data.get("thread_id", "unknown"))