
from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Text, ForeignKey, DECIMAL
from sqlalchemy.orm import relationship
from infrastructure.connection.base import Base

class Ticket(Base):
    """tickets表"""
    __tablename__ = 'tickets'

    # 主键ID
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 机票编号
    ticket_no = Column(String(255), nullable=False)
    
    # 订票参考号
    book_ref = Column(String(255), nullable=True)
    
    # 乘客ID
    passenger_id = Column(String(255), nullable=False)