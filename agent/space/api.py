import uvicorn
from fastapi import FastAPI, HTTPException, APIRouter, WebSocket
from fastapi.middleware.cors import CORSMiddleware  # 导入 CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any
from starlette.websockets import WebSocketDisconnect
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

from infrastructure.config import config
from infrastructure.logger import log
from agent.space.space_agent import app
from agent.space.utils.websocket_helper import WebSocketMessageHandler

class InvokeRequest(BaseModel):
    input: str
    thread_id: str

# 定义 API 响应体模型 (可以根据需要扩展)
class InvokeResponse(BaseModel):
    output: dict
    thread_id: str
    # 可以添加其他需要返回的状态信息
    # final_state: Dict[str, Any]

# --- 创建 API Router ---
api_prefix = config.get("api.prefix", "/api")
api_version = config.get("api.version", "v1")
router_prefix = f"{api_prefix}/{api_version}/space" # 为 space agent 定义特定的子路径

# 创建一个 APIRouter 实例
router = APIRouter(
    prefix=router_prefix,
    tags=["Space Agent"], # 为 Swagger UI 添加标签
)


# --- 将原来的 API 端点定义移到 Router 下 ---
@router.post("/invoke", response_model=InvokeResponse)
async def invoke_agent(request: InvokeRequest):
    """
    调用 Space Agent 处理用户输入。
    """
    thread_id = request.thread_id
    user_input = request.input
    log.info(f"Received invoke request for thread_id: {thread_id}") # 添加日志

    if not thread_id:
        log.warn("Invoke request missing thread_id") # 添加日志
        raise HTTPException(status_code=400, detail="thread_id is required")

    # 配置 LangGraph 调用，使用请求中提供的 thread_id
    config_invoke = {"configurable": {"thread_id": thread_id}} # 避免与全局 config 变量名冲突

    # 准备输入
    inputs = {"messages": [HumanMessage(content=user_input)], "user_input": user_input}

    try:
        # 使用 invoke 获取最终结果 (非流式)
        final_state = app.invoke(inputs, config_invoke)
        # 使用 lambda 表达式从最终状态中过滤掉 HumanMessage
        if final_state and "messages" in final_state:
            if len(final_state["messages"]) > 0:
                final_state["messages"] = [final_state["messages"][-1]]

        log.info(f"Sending response for thread_id: {thread_id}") # 添加日志
        return InvokeResponse(output={**final_state}, thread_id=thread_id)

    except Exception as e:
        log.error(f"Error invoking agent for thread {thread_id}: {e}", exc_info=True) # 使用日志记录器并包含堆栈跟踪
        raise HTTPException(status_code=500, detail=f"Agent invocation failed: {str(e)}")

@router.get("/get_state/{thread_id}")
async def get_thread_state(thread_id: str):
    """
    获取指定对话线程的当前状态。
    """
    log.info(f"Received get_state request for thread_id: {thread_id}") # 添加日志
    config_state = {"configurable": {"thread_id": thread_id}} # 避免与全局 config 变量名冲突
    try:
        state = app.get_state(config_state)
        if state:
            log.debug(f"State found for thread {thread_id}") # 添加日志
            # 注意：直接返回 state.values 可能包含复杂对象，需要序列化处理
            # 考虑只返回必要的信息或进行转换
            return {"thread_id": thread_id, "state_exists": True, "current_values_keys": list(state.values.keys())} # 示例：只返回键
        else:
            log.debug(f"No state found for thread {thread_id}") # 添加日志
            return {"thread_id": thread_id, "state_exists": False}
    except Exception as e:
        log.error(f"Error getting state for thread {thread_id}: {e}", exc_info=True) # 使用日志记录器
        raise HTTPException(status_code=500, detail=f"Failed to get state: {str(e)}")


# --- 创建主 FastAPI 应用实例 ---
# 不再在主应用上设置 title 等，可以在需要时设置
api = FastAPI(
    title="AI Agent Enterprise API", # 可以设置一个更通用的标题
    description="Main API for AI Agent Enterprise services.",
    version=config.get("application.version", "1.0.0") # 从配置读取应用版本
)

# --- 配置 CORS ---
# 定义允许访问的源列表
# 在开发环境中，可以使用 "*" 允许所有源，但在生产环境中应指定具体的前端源
origins = [
    "http://localhost:8081", # 允许您的前端源
    "http://localhost",      # 如果有其他本地源需要访问
    # "https://your-production-frontend.com" # 生产环境的前端地址
]

# 添加 CORSMiddleware 到 FastAPI 应用
api.add_middleware(
    CORSMiddleware,
    allow_origins=origins, # 允许访问的源
    allow_credentials=True, # 是否支持 cookie 跨域 (如果需要)
    allow_methods=["*"],    # 允许所有方法 (GET, POST, PUT, DELETE 等) 或指定 ["GET", "POST"]
    allow_headers=["*"],    # 允许所有请求头 或指定需要的头
)


# --- 将 Router 包含到主应用中 ---
api.include_router(router)
@api.websocket("/ws/space")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    handler = WebSocketMessageHandler(websocket, app)
    while True:
        try:
            data = await websocket.receive_json()
            msg_type = data.get("type")
            
            if msg_type == "tool_result":
                await handler.handle_tool_result(data)
            elif msg_type == "user_input":
                await handler.process_event_stream(user_input=data["content"], thread_id=data["thread_id"])
            else:
                log.warn(f"未知消息类型: {msg_type}")
                await handler.send_message("error", f"未知消息类型: {msg_type}", data.get("thread_id", "unknown"))
                
        except WebSocketDisconnect:
            log.info("WebSocket 客户端断开连接")
            break
        except Exception as e:
            log.error(f"WebSocket 处理错误: {e}")
            await websocket.send_json({"type": "error", "message": str(e)})

# --- 主程序入口 ---
if __name__ == "__main__":
    server_host = config.get("server.host")
    server_port = config.get("server.port")
    log.info(f"Starting server on {server_host}:{server_port}") # 添加启动日志

    # 使用从配置读取的值启动 uvicorn
    uvicorn.run(
        "agent.space.api:api", # 指向 FastAPI 应用实例
        host=server_host,
        port=int(server_port), #确保端口是整数
        reload=True, # 开发时可以保留 reload
        log_level=config.get("logging.level", "info").lower() # 从配置读取日志级别
    )