from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from starlette import status

from config import CONFIG,get_logger
from starlette.requests import Request
from utils.jwt_utils import create_token
from utils.password_hash import get_hashed_password, verify_password
from api.graph_api.graph_schemas import BaseGraphSchema, GraphResponseSchema
from app.multi_agent.workflow.primary_workflow import build_primary_workflow
from app.multi_agent.workflow.init_db import update_dates
from langchain_core.messages import ToolMessage,AIMessage
from app.multi_agent.workflow.base import print_event

# 创建分路由
router = APIRouter()

logger = get_logger(__name__)

graph = build_primary_workflow()
INTERRUPT_NODES = {
    "hotel_write_tools",
    "flight_write_tools",
    "car_rental_write_tools",
    "trip_write_tools",
}

_printed = set()    
@router.post('/graph/', description='执行工作流', summary='执行工作流', response_model=GraphResponseSchema)
def execute_graph(request: Request, obj_in: BaseGraphSchema):
    logger.info(f'登录之后的用户名：{request.state.username}')  # 从request.state中获取用户信息, 在auth_middleware中设置的数据结构
    user_input = obj_in.user_input
    config = obj_in.config.model_dump()
    
    result = ''
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
    
    return GraphResponseSchema( assistant=result )



