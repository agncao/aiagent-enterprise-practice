"""
seats 数据模型
自动生成于 models
"""
from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Text, ForeignKey, DECIMAL
from sqlalchemy.orm import relationship
from infrastructure.connection.base import Base


class Seat(Base):
    """seats表"""
    __tablename__ = 'seats'

    # 主键ID
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 飞机编号
    aircraft_code = Column(String(255), nullable=False)
    
    # 座位号
    seat_no = Column(String(255), nullable=False)
    
    # 舱位等级
    fare_conditions = Column(String(255), nullable=True)
