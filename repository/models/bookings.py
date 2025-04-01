"""
bookings 数据模型
自动生成于 models
"""
from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Text, ForeignKey, DECIMAL
from sqlalchemy.orm import relationship
from infrastructure.connection.base import Base

class Booking(Base):
    """bookings表"""
    __tablename__ = 'bookings'


    book_ref = Column(Integer, primary_key=True, autoincrement=True)

    book_date = Column(DateTime, )
    total_amount = Column(Integer(255), )
