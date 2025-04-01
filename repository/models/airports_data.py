"""
airports_data 数据模型
自动生成于 models
"""
from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Text, ForeignKey, DECIMAL
from sqlalchemy.orm import relationship
from infrastructure.connection.base import Base

class AirportsData(Base):
    """airports_data表"""
    __tablename__ = 'airports_data'


    airport_code = Column(String(255), primary_key=True)

    airport_name = Column(String(255), nullable=True, )

    city = Column(String(255), nullable=True,)

    coordinates = Column(String(255), )

    timezone = Column(String(255), )
