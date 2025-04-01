"""
ticket_flights 数据模型
自动生成于 models
"""
from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Text, ForeignKey, DECIMAL
from sqlalchemy.orm import relationship
from infrastructure.connection.base import Base


class TicketFlight(Base):
    """ticket_flights表"""
    __tablename__ = 'ticket_flights'

    # 主键ID
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 机票编号
    ticket_no = Column(String(255), nullable=False)

    # 航班ID
    flight_id = Column(String(255), nullable=False)

    # 票价类型
    fare_conditions = Column(String(255), nullable=True)
    # 票价金额
    amount = Column(Float(precision=10, decimal_return_scale=2), nullable=False)

