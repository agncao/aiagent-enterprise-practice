"""
hotels 数据模型
自动生成于 models
"""
from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Text, ForeignKey, DECIMAL
from sqlalchemy.orm import relationship
from infrastructure.connection.base import Base

class Hotel(Base):
    """hotels表"""
    __tablename__ = 'hotels'
    # ID，主键，自增
    id = Column(Integer, primary_key=True, autoincrement=True)
    # 酒店名称
    name = Column(String(255), nullable=False)
    # 酒店位置
    location = Column(String(255), nullable=True)
    # 价格等级
    price_tier = Column(String(255), nullable=True)
    # 入住日期
    checkin_date = Column(DateTime, nullable=True)
    # 退房日期
    checkout_date = Column(DateTime, nullable=True)
    # 是否已预订（0未预订，1已预订）
    booked = Column(Integer, nullable=False, default=0)

