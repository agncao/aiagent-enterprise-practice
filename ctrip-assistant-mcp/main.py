## http://localhost:8000/docs  # 访问接口文档

## 使用 MCP 官方 Inspector 工具调试
## 步骤1: 启动你的 FastAPI 业务应用 （包含了 SSE MCP）：python main.py
## 步骤2: 启动 MCP Inspector 并连接到你的 SSE 服务 ：
##      打开一个新的终端，使用 npx 运行 inspector，并指定 SSE 端的 URL:
##          命令: npx @modelcontextprotocol/inspector sse "http://127.0.0.1:8000/mcp/sse"
## 步骤3: 在浏览器中测试
##      Inspector 启动后，会提示你在浏览器中打开一个地址（通常是 http://localhost:5173 ）。
#       打开后，你就能在可视化界面中看到你发布的所有工具（如 mcp_search_flights 、 mcp_search_hotels 等），并可以直接在界面上填写参数点击运行，查看 JSON 返回结果。

from pathlib import Path

import uvicorn
from fastapi import FastAPI, Depends
from starlette.staticfiles import StaticFiles
from config import CONFIG, get_logger
from utils import handler_error, cors, middlewares

from api import routers
from utils.docs_oauth2 import MyOAuth2PasswordBearer
from mcp_server import mcp

logger = get_logger(__name__)


class Server:

    def __init__(self):
        # 创建自定义的OAuth2的实例
        my_oauth2 = MyOAuth2PasswordBearer(tokenUrl='/api/auth/', schema='JWT')
        # # 添加全局的依赖: 让所有的接口，都拥有接口文档的认证
        self.app = FastAPI(dependencies=[Depends(my_oauth2)])

        # 把项目下的static目录作为静态文件的访问目录
        static_dir = Path(__file__).resolve().parent / "static"
        if static_dir.exists():
            self.app.mount('/static', StaticFiles(directory=str(static_dir)), name='my_static')
            logger.info("静态资源目录已挂载: %s", static_dir)
        else:
            logger.warning("静态资源目录不存在，已跳过挂载: %s", static_dir)
        self.init_app()

    def init_app(self):
        # 初始化全局异常处理
        handler_error.init_handler_errors(self.app)
        # 初始化全局中间件
        middlewares.init_middleware(self.app)
        # 初始化全局CORS跨域的处理
        cors.init_cors(self.app)
        # 初始化主路由
        routers.init_routers(self.app)
        # 将 MCP 服务以 SSE 的形式挂载到现有 FastAPI 应用中
        self.app.mount('/mcp', mcp.sse_app())
        logger.info("MCP 服务已挂载至 /mcp/sse (SSE endpoint) 和 /mcp/messages/ (POST endpoint)")

    def run(self):
        server_config = CONFIG["server"].get("api", CONFIG["server"])
        host = server_config.get("host", "127.0.0.1")
        port = server_config.get("port", 8000)
        reload = server_config.get("reload", False)
        if reload:
            uvicorn.run(
                "main:app",
                host=host,
                port=port,
                reload=reload,
            )
            return
        uvicorn.run(
            app=self.app,
            host=host,
            port=port,
            reload=reload,
        )


server = Server()
app = server.app


if __name__ == '__main__':
    server.run()