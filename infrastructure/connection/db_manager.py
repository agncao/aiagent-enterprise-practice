"""
数据库连接池管理模块
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from infrastructure.connection.base import Base
import logging

from infrastructure.connection.database import DB_URL

# 创建日志记录器
logger = logging.getLogger(__name__)

class DatabaseManager:
    """数据库连接池管理类"""
    
    _instance = None
    
    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """初始化数据库连接池"""
        if self._initialized:
            return
            
        try:
            # 创建数据库引擎
            self.engine = create_engine(
                DB_URL,
                pool_size=10,  # 连接池大小
                max_overflow=20,  # 最大溢出连接数
                pool_recycle=3600,  # 连接回收时间（秒）
                pool_pre_ping=True,  # 连接前ping
                echo=False  # 是否打印SQL语句
            )
            
            # 创建会话工厂
            self.session_factory = sessionmaker(bind=self.engine)
            
            # 创建线程安全的会话
            self.Session = scoped_session(self.session_factory)
            
            # 初始化标志
            self._initialized = True
            
            logger.info("数据库连接池初始化成功")
        except Exception as e:
            logger.error(f"数据库连接池初始化失败: {str(e)}")
            raise
    
    def create_tables(self):
        """创建所有表"""
        Base.metadata.create_all(self.engine)
        logger.info("数据库表创建成功")
    
    def get_session(self):
        """获取数据库会话"""
        return self.Session()
    
    def close_session(self, session):
        """关闭数据库会话"""
        if session:
            session.close()
    
    def close_all_sessions(self):
        """关闭所有会话"""
        self.Session.remove()