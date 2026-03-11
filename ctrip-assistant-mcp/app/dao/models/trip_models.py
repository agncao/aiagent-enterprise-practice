"""旅行推荐数据模型"""
from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

# 从 flight_models 导入 Base
from .flight_models import Base


class TripRecommendation(Base):
    """旅行推荐表"""
    __tablename__ = "trip_recommendations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(300), comment="推荐项目名称")
    location: Mapped[str] = mapped_column(String(200), comment="位置")
    keywords: Mapped[str] = mapped_column(Text, comment="关键词")
    details: Mapped[str] = mapped_column(Text, comment="详细信息")
    booked: Mapped[int] = mapped_column(Integer, default=0, comment="是否已预订")

    def __repr__(self):
        return f"<TripRecommendation(id={self.id}, name={self.name}, location={self.location})>"
