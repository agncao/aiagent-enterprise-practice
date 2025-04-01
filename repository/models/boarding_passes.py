"""
boarding_passes 数据模型
自动生成于 models
"""
from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Text, ForeignKey, DECIMAL
from sqlalchemy.orm import relationship
from infrastructure.connection.base import Base

class BoardingPass(Base):
    """boarding_passes表"""
    __tablename__ = 'boarding_passes'

    id = Column(Integer, primary_key=True)
    ticket_no = Column(String(255), nullable=False)

    flight_id = Column(String(255), nullable=False)

    boarding_no = Column(String(255), )

    seat_no = Column(String(255), )
