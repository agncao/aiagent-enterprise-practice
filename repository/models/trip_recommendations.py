
"""
旅行推荐表
包含以下字段:
- id: 主键，自增
- name: 推荐名称
- location: 地点
- keywords: 关键词
- details: 详细信息
- booked: 预订次数
"""
from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Text, ForeignKey, DECIMAL
from sqlalchemy.orm import relationship
from infrastructure.connection.base import Base

class TripRecommendation(Base):
    """trip_recommendations旅行"""
    __tablename__ = 'trip_recommendations'

    # 主键ID，自增
    id = Column(Integer, primary_key=True, autoincrement=True)
    # 主键ID，自增
    id = Column(Integer, primary_key=True, autoincrement=True)
    # 推荐名称
    name = Column(String(255), nullable=False)
    # 地点
    location = Column(String(255), nullable=False)
    # 关键词
    keywords = Column(String(255), nullable=True)
    # 详细信息
    details = Column(String(255), nullable=True)
    # 预订次数
    booked = Column(Integer, nullable=False, default=0)
