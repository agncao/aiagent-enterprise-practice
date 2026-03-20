"""基础仓储类"""
from typing import Any, Generic, TypeVar

from pydantic import BaseModel

from .session import get_session

ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class BaseRepository(Generic[ModelType]):
    """基础仓储类，提供通用的CRUD操作"""

    def __init__(self, model: type[ModelType]) -> None:
        """初始化仓储

        Args:
            model: SQLAlchemy模型类
        """
        self.model = model

    def get(self, id: int) -> ModelType | None:
        """根据ID获取单条记录

        Args:
            id: 记录ID

        Returns:
            模型实例或None
        """
        with get_session() as session:
            return session.query(self.model).filter(self.model.id == id).first()

    def get_by(
        self, **filters: Any
    ) -> ModelType | None:
        """根据条件获取单条记录

        Args:
            **filters: 过滤条件

        Returns:
            模型实例或None
        """
        with get_session() as session:
            query = session.query(self.model)
            for key, value in filters.items():
                if hasattr(self.model, key):
                    query = query.filter(getattr(self.model, key) == value)
            return query.first()

    def list(
        self,
        skip: int = 0,
        limit: int = 100,
        **filters: Any,
    ) -> list[ModelType]:
        """获取记录列表

        Args:
            skip: 跳过记录数
            limit: 返回记录数
            **filters: 过滤条件

        Returns:
            模型实例列表
        """
        with get_session() as session:
            query = session.query(self.model)
            for key, value in filters.items():
                if hasattr(self.model, key):
                    query = query.filter(getattr(self.model, key) == value)
            return query.offset(skip).limit(limit).all()

    def create(self, obj_in: dict[str, Any]) -> ModelType:
        """创建新记录

        Args:
            obj_in: 创建数据字典

        Returns:
            创建的模型实例
        """
        with get_session() as session:
            db_obj = self.model(**obj_in)
            session.add(db_obj)
            session.commit()
            session.refresh(db_obj)
            return db_obj

    def update(
        self,
        id: int,
        obj_in: dict[str, Any],
    ) -> ModelType | None:
        """更新记录

        Args:
            id: 记录ID
            obj_in: 更新数据字典

        Returns:
            更新后的模型实例或None
        """
        with get_session() as session:
            db_obj = session.query(self.model).filter(self.model.id == id).first()
            if db_obj is None:
                return None

            for field, value in obj_in.items():
                if hasattr(db_obj, field):
                    setattr(db_obj, field, value)

            session.commit()
            session.refresh(db_obj)
            return db_obj

    def delete(self, id: int) -> bool:
        """删除记录

        Args:
            id: 记录ID

        Returns:
            是否删除成功
        """
        with get_session() as session:
            db_obj = session.query(self.model).filter(self.model.id == id).first()
            if db_obj is None:
                return False

            session.delete(db_obj)
            session.commit()
            return True

    def count(self, **filters: Any) -> int:
        """统计记录数

        Args:
            **filters: 过滤条件

        Returns:
            记录数量
        """
        with get_session() as session:
            query = session.query(self.model)
            for key, value in filters.items():
                if hasattr(self.model, key):
                    query = query.filter(getattr(self.model, key) == value)
            return query.count()

    def exists(self, **filters: Any) -> bool:
        """检查记录是否存在

        Args:
            **filters: 过滤条件

        Returns:
            是否存在
        """
        return self.count(**filters) > 0
