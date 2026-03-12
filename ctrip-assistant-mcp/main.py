## http://localhost:8000/docs  # 访问接口文档

from pathlib import Path

import uvicorn
from fastapi import FastAPI, Depends
from starlette.staticfiles import StaticFiles
from config import CONFIG, get_logger
from utils import handler_error, cors, middlewares

from api import routers
from utils.docs_oauth2 import MyOAuth2PasswordBearer

logger = get_logger(__name__)


class Server:

    def __init__(self):
        # 创建自定义的OAuth2的实例
        my_oauth2 = MyOAuth2PasswordBearer(tokenUrl='/api/auth/', schema='JWT')
        # 添加全局的依赖: 让所有的接口，都拥有接口文档的认证
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