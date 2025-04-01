"""
aircrafts_data 数据模型
自动生成于 models
"""
from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Text, ForeignKey, DECIMAL
from sqlalchemy.orm import relationship
from infrastructure.connection.base import Base

class AircraftsData(Base):
    """aircrafts_data表"""
    __tablename__ = 'aircrafts_data'


    aircraft_code = Column(String(255), primary_key=True, nullable=False, )

    model = Column(String(255), nullable=False, )

    range = Column(String(255), nullable=False, )
