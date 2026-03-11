"""航班相关数据模型"""
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, inspect
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from .base_model import Base


class AircraftData(Base):
    """飞机机型表"""
    __tablename__ = "aircrafts_data"

    aircraft_code: Mapped[str] = mapped_column(String(10), primary_key=True)
    model: Mapped[str] = mapped_column(String(100), comment="机型名称")
    range: Mapped[int] = mapped_column(Integer, comment="飞行范围（公里）")

    seats: Mapped[list["Seat"]] = relationship("Seat", back_populates="aircraft")

    def __repr__(self):
        return f"<AircraftData(aircraft_code={self.aircraft_code}, model={self.model})>"


class AirportData(Base):
    """机场表"""
    __tablename__ = "airports_data"

    airport_code: Mapped[str] = mapped_column(String(10), primary_key=True)
    airport_name: Mapped[str] = mapped_column(String(200), comment="机场名称")
    city: Mapped[str] = mapped_column(String(100), comment="城市")
    coordinates: Mapped[str] = mapped_column(String(100), comment="坐标")
    timezone: Mapped[str] = mapped_column(String(50), comment="时区")

    def __repr__(self):
        return f"<AirportData(airport_code={self.airport_code}, airport_name={self.airport_name}, city={self.city})>"


class Flight(Base):
    """航班表"""
    __tablename__ = "flights"

    flight_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    flight_no: Mapped[str] = mapped_column(String(20), comment="航班号")
    scheduled_departure: Mapped[datetime | None] = mapped_column(DateTime, comment="计划出发时间")
    scheduled_arrival: Mapped[datetime | None] = mapped_column(DateTime, comment="计划到达时间")
    departure_airport: Mapped[str] = mapped_column(
        String(10),
        ForeignKey("airports_data.airport_code"),
        comment="出发机场代码",
    )
    arrival_airport: Mapped[str] = mapped_column(
        String(10),
        ForeignKey("airports_data.airport_code"),
        comment="到达机场代码",
    )
    status: Mapped[str] = mapped_column(String(20), comment="航班状态")
    aircraft_code: Mapped[str] = mapped_column(
        String(10),
        ForeignKey("aircrafts_data.aircraft_code"),
        comment="机型代码",
    )
    actual_departure: Mapped[datetime | None] = mapped_column(DateTime, comment="实际出发时间")
    actual_arrival: Mapped[datetime | None] = mapped_column(DateTime, comment="实际到达时间")

    departure_airport_rel: Mapped["AirportData"] = relationship(
        "AirportData", foreign_keys=[departure_airport]
    )
    arrival_airport_rel: Mapped["AirportData"] = relationship(
        "AirportData", foreign_keys=[arrival_airport]
    )
    aircraft_rel: Mapped["AircraftData"] = relationship(
        "AircraftData", foreign_keys=[aircraft_code]
    )

    def __repr__(self):
        return f"<Flight(flight_id={self.flight_id}, flight_no={self.flight_no}, {self.departure_airport}->{self.arrival_airport})>"


class Seat(Base):
    """飞机座位表"""
    __tablename__ = "seats"

    aircraft_code: Mapped[str] = mapped_column(
        String(10),
        ForeignKey("aircrafts_data.aircraft_code"),
        primary_key=True,
    )
    seat_no: Mapped[str] = mapped_column(String(10), primary_key=True, comment="座位号")
    fare_conditions: Mapped[str] = mapped_column(String(20), comment="票价条件")

    aircraft: Mapped["AircraftData"] = relationship("AircraftData", back_populates="seats")

    def __repr__(self):
        return f"<Seat(aircraft_code={self.aircraft_code}, seat_no={self.seat_no})>"
