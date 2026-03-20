"""数据库连接管理"""
from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from config import CONFIG

# 同步引擎和会话工厂
_sync_engine = None
_sync_session_factory = None


def get_sync_engine():
    """获取同步数据库引擎"""
    global _sync_engine
    if _sync_engine is None:
        conn_str = f"{CONFIG['database']['dialect']}:///{CONFIG['database']['url']}"  # SQLite 连接格式
        _sync_engine = create_engine(
            conn_str,
            echo=CONFIG["database"]["echo"],
            pool_size=CONFIG["database"]["pool_size"],
            max_overflow=CONFIG["database"]["max_overflow"],
            pool_recycle=CONFIG["database"]["pool_recycle"],
            pool_pre_ping=False,  # SQLite 不支持pool_pre_ping，设为false
            connect_args={"check_same_thread": False}  # SQLite 多线程访问必须加此参数
        )

        # SQLite优化
        if "sqlite" == CONFIG["database"]["dialect"]:
            @event.listens_for(_sync_engine, "connect")
            def set_sqlite_pragma(dbapi_conn, connection_record):
                cursor = dbapi_conn.cursor()
                cursor.execute("PRAGMA journal_mode=WAL")  # 写前日志模式
                cursor.execute("PRAGMA synchronous=NORMAL")  # 同步模式
                cursor.execute("PRAGMA cache_size=-64000")  # 64MB缓存
                cursor.execute("PRAGMA foreign_keys=ON")  # 开启外键
                cursor.close()

    return _sync_engine


def get_sync_session_factory():
    """获取同步会话工厂"""
    global _sync_session_factory
    if _sync_session_factory is None:
        engine = get_sync_engine()
        _sync_session_factory = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=engine,
        )
    return _sync_session_factory


def init_db():
    """初始化数据库"""
    engine = get_sync_engine()
    # 这里可以添加创建表的操作
    # Base.metadata.create_all(bind=engine)


@contextmanager
def get_session() -> Generator[Session]:
    """获取同步数据库会话上下文管理器

    Yields:
        Session: SQLAlchemy会话
    """
    session_factory = get_sync_session_factory()
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


def get_db() -> Session:
    """获取数据库会话（用于依赖注入）

    Returns:
        Session: SQLAlchemy会话
    """
    session_factory = get_sync_session_factory()
    return session_factory()

