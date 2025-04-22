import uvicorn
from fastapi import FastAPI, HTTPException, APIRouter, WebSocket
# 导入 CORSMiddleware
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any

from agent.space.space_agent import app, memory
from langchain_core.messages import HumanMessage, AIMessage
# 导入配置模块
from infrastructure.config import config
from infrastructure.logger import log # 导入日志记录器

# 定义 API 请求体模型
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

# 新增WebSocket端点
@api.websocket("/ws/space")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            # 等待前端发送消息
            data = await websocket.receive_json()
            user_input = data.get("input")
            thread_id = data.get("thread_id")
            if not user_input or not thread_id:
                await websocket.send_json({"error": "input and thread_id required"})
                continue

            config_invoke = {"configurable": {"thread_id": thread_id}}
            inputs = {"messages": [HumanMessage(content=user_input)], "user_input": user_input}

            # 实时流式返回agent执行过程
            try:
                # 使用LangGraph的stream方法，逐步推送每个事件
                for event in app.stream(inputs, config_invoke, stream_mode="values"):
                    # 只推送agent节点的AI回复和工具节点的结果
                    if "messages" in event and len(event["messages"]) > 0:
                        last_message = event["messages"][-1]
                        if isinstance(last_message, AIMessage):
                            await websocket.send_json({
                                "type": "ai_message",
                                "content": last_message.content,
                                "thread_id": thread_id
                            })
                    # 你也可以根据event内容推送工具调用的结果
                    if "tool_func" in event:
                        await websocket.send_json({
                            "type": "tool_call",
                            "tool_func": event["tool_func"],
                            "tool_func_args": event.get("tool_func_args"),
                            "thread_id": thread_id
                        })
                # 结束标志
                await websocket.send_json({"type": "end", "thread_id": thread_id})
            except Exception as e:
                log.error(f"WebSocket agent error: {e}")
                await websocket.send_json({"error": str(e)})
    except WebSocketDisconnect:
        log.info("WebSocket disconnected")