from sqlalchemy import inspect, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    """声明式基类"""
    def to_dict(self) -> dict:
        return {column.key: getattr(self, column.key) for column in inspect(self).mapper.column_attrs}