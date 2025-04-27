"""
SQLite 持久化存储层，用于保存 LangGraph 的 checkpoint 数据。
实现了 LangGraph Checkpointer 接口，可以直接用于 LangGraph 工作流。
"""

import json
import sqlite3
import pickle
from typing import Any, Dict, Optional, List
from datetime import datetime
from pathlib import Path
from langchain_core.messages import BaseMessage,messages_from_dict, messages_to_dict
from infrastructure.logger import log
from infrastructure.config import config

class SQLiteStorage:
    """SQLite 数据访问层，提供基本的 CRUD 操作"""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        初始化 SQLite 存储
        
        Args:
            db_path: SQLite 数据库文件路径，如果为 None，则使用默认路径
        """
        if db_path is None:
            # 使用项目根目录下的 data 目录
            project_root = Path(__file__).parent.parent.parent.parent
            data_dir = project_root / "data"
            data_dir.mkdir(exist_ok=True)
            db_path = str(data_dir / "langgraph.db")
        
        self.db_path = db_path
    
    def _get_connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_db(self):
        """初始化数据库表结构"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            
            # 创建 checkpoints 表，用于存储工作流状态
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS checkpoints (
                thread_id TEXT PRIMARY KEY,
                state BLOB NOT NULL,
                metadata TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            ''')
            
            # 创建 messages 表，用于存储消息历史
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                thread_id TEXT NOT NULL,
                message BLOB NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (thread_id) REFERENCES checkpoints (thread_id)
            )
            ''')
            
            conn.commit()
            log.info(f"SQLite 数据库初始化完成: {self.db_path}")
        except Exception as e:
            log.error(f"SQLite 数据库初始化失败: {e}")
            raise
        finally:
            conn.close()
    
    def save_checkpoint(self, thread_id: str, state: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        保存工作流状态
        
        Args:
            thread_id: 会话 ID
            state: 工作流状态
            metadata: 元数据
            
        Returns:
            bool: 保存是否成功
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            now = datetime.now().isoformat()
            
            # 序列化状态
            state_blob = pickle.dumps(state)
            metadata_json = json.dumps(metadata or {})
            
            # 检查是否已存在
            cursor.execute("SELECT 1 FROM checkpoints WHERE thread_id = ?", (thread_id,))
            exists = cursor.fetchone() is not None
            
            if exists:
                # 更新现有记录
                cursor.execute(
                    "UPDATE checkpoints SET state = ?, metadata = ?, updated_at = ? WHERE thread_id = ?",
                    (state_blob, metadata_json, now, thread_id)
                )
            else:
                # 插入新记录
                cursor.execute(
                    "INSERT INTO checkpoints (thread_id, state, metadata, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                    (thread_id, state_blob, metadata_json, now, now)
                )
            
            # 保存消息历史
            if "messages" in state and isinstance(state["messages"], list):
                self._save_messages(cursor, thread_id, state["messages"])
            
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            log.error(f"保存 checkpoint 失败: {e}")
            return False
        finally:
            conn.close()
    
    def _save_messages(self, cursor: sqlite3.Cursor, thread_id: str, messages: List[BaseMessage]):
        """保存消息历史"""
        now = datetime.now().isoformat()
        
        # 将消息转换为可序列化格式
        messages_data = messages_to_dict(messages)
        messages_blob = pickle.dumps(messages_data)
        
        # 删除旧消息
        cursor.execute("DELETE FROM messages WHERE thread_id = ?", (thread_id,))
        
        # 插入新消息
        cursor.execute(
            "INSERT INTO messages (thread_id, message, created_at) VALUES (?, ?, ?)",
            (thread_id, messages_blob, now)
        )
    
    def get_checkpoint(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """
        获取工作流状态
        
        Args:
            thread_id: 会话 ID
            
        Returns:
            Optional[Dict[str, Any]]: 工作流状态，如果不存在则返回 None
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            
            # 获取状态
            cursor.execute("SELECT state FROM checkpoints WHERE thread_id = ?", (thread_id,))
            row = cursor.fetchone()
            
            if row is None:
                return None
            
            # 反序列化状态
            state = pickle.loads(row["state"])
            
            # 获取消息历史
            cursor.execute("SELECT message FROM messages WHERE thread_id = ?", (thread_id,))
            message_row = cursor.fetchone()
            
            if message_row is not None:
                messages_data = pickle.loads(message_row["message"])
                messages = messages_from_dict(messages_data)
                state["messages"] = messages
            
            return state
        except Exception as e:
            log.error(f"获取 checkpoint 失败: {e}")
            return None
        finally:
            conn.close()
    
    def list_checkpoints(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        列出所有 checkpoint
        
        Args:
            limit: 返回的最大数量
            offset: 起始偏移量
            
        Returns:
            List[Dict[str, Any]]: checkpoint 列表
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT thread_id, metadata, created_at, updated_at FROM checkpoints ORDER BY updated_at DESC LIMIT ? OFFSET ?",
                (limit, offset)
            )
            
            result = []
            for row in cursor.fetchall():
                result.append({
                    "thread_id": row["thread_id"],
                    "metadata": json.loads(row["metadata"]),
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"]
                })
            
            return result
        except Exception as e:
            log.error(f"列出 checkpoints 失败: {e}")
            return []
        finally:
            conn.close()
    
    def delete_checkpoint(self, thread_id: str) -> bool:
        """
        删除 checkpoint
        
        Args:
            thread_id: 会话 ID
            
        Returns:
            bool: 删除是否成功
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            
            # 删除消息
            cursor.execute("DELETE FROM messages WHERE thread_id = ?", (thread_id,))
            
            # 删除状态
            cursor.execute("DELETE FROM checkpoints WHERE thread_id = ?", (thread_id,))
            
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            conn.rollback()
            log.error(f"删除 checkpoint 失败: {e}")
            return False
        finally:
            conn.close()


class SQLiteCheckpointer(SQLiteStorage):
    """实现 LangGraph Checkpointer 接口的 SQLite 存储"""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        初始化 SQLite Checkpointer
        
        Args:
            db_path: SQLite 数据库文件路径，如果为 None，则使用默认路径
        """
        self.storage = SQLiteStorage(db_path)
    
    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        """
        获取状态
        
        Args:
            key: 状态键（会话 ID）
            
        Returns:
            Optional[Dict[str, Any]]: 状态，如果不存在则返回 None
        """
        return self.storage.get_checkpoint(key)
    
    async def put(self, key: str, state: Dict[str, Any]) -> None:
        """
        保存状态
        
        Args:
            key: 状态键（会话 ID）
            state: 状态
        """
        self.storage.save_checkpoint(key, state)
    
    async def delete(self, key: str) -> None:
        """
        删除状态
        
        Args:
            key: 状态键（会话 ID）
        """
        self.storage.delete_checkpoint(key)
    
    # 同步版本的方法，用于非异步环境
    def get_sync(self, key: str) -> Optional[Dict[str, Any]]:
        """同步版本的 get 方法"""
        return self.storage.get_checkpoint(key)
    
    def put_sync(self, key: str, state: Dict[str, Any]) -> None:
        """同步版本的 put 方法"""
        self.storage.save_checkpoint(key, state)
    
    def delete_sync(self, key: str) -> None:
        """同步版本的 delete 方法"""
        self.storage.delete_checkpoint(key)

if __name__ == "__main__":
    storage = SQLiteStorage()
    storage.init_db()
    checkpointer = SQLiteCheckpointer()
    # 测试
    checkpointer.put_sync("test_thread", {"messages": []})
