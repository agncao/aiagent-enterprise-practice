"""
car_rentals 数据模型
自动生成于 models
"""
from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Text, ForeignKey, DECIMAL
from sqlalchemy.orm import relationship
from infrastructure.connection.base import Base

class CarRental(Base):
    """car_rentals表"""
    __tablename__ = 'car_rentals'

    # 主键ID，自增
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 租车名称
    name = Column(String(255), nullable=True)
    
    # 位置信息
    location = Column(String(255), nullable=True)
    
    # 价格等级
    price_tier = Column(String(255), nullable=True)
    
    # 开始时间
    start_date = Column(DateTime, nullable=True)
    
    # 结束时间
    end_date = Column(DateTime, nullable=True)
    
    # 是否已预订，0未预订，1已预订
    booked = Column(Integer, nullable=False, default=0)
