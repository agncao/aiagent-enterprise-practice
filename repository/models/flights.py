"""
航班数据模型
"""
from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey
from sqlalchemy.orm import relationship
from infrastructure.connection.base import Base

class Flight(Base):
    """航班信息表"""
    __tablename__ = 'flights'

    flight_id = Column(Integer, primary_key=True, autoincrement=True)
    flight_no = Column(String(255), nullable=True)
    scheduled_departure = Column(String(255), nullable=True)
    scheduled_arrival = Column(String(255), nullable=True)
    departure_airport = Column(String(255), nullable=True)
    arrival_airport = Column(String(255), nullable=True)
    status = Column(String(255), nullable=True)
    aircraft_code = Column(String(255), nullable=True)
    actual_departure = Column(String(255), nullable=True)
    actual_arrival = Column(String(255), nullable=True)

    def __repr__(self):
        return f'<Flight(flight_id={self.flight_id}, flight_no={self.flight_no}, departure={self.departure_airport}, arrival={self.arrival_airport})>'
