"""预订相关数据模型"""
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

# 从 flight_models 导入 Base
from .flight_models import Base


class Booking(Base):
    """预订表"""
    __tablename__ = "bookings"

    book_ref = Column(String(10), primary_key=True)
    book_date = Column(DateTime, comment="预订日期")
    total_amount = Column(Integer, comment="总金额")

    tickets = relationship("Ticket", back_populates="booking")

    def __repr__(self):
        return f"<Booking(book_ref={self.book_ref}, total_amount={self.total_amount})>"


class Ticket(Base):
    """机票表"""
    __tablename__ = "tickets"

    ticket_no = Column(String(20), primary_key=True)
    book_ref = Column(String(10), ForeignKey("bookings.book_ref"), comment="预订编号")
    passenger_id = Column(String(20), comment="乘客ID")

    booking = relationship("Booking", back_populates="tickets")
    ticket_flights = relationship("TicketFlight", back_populates="ticket", cascade="all, delete-orphan")
    boarding_passes = relationship("BoardingPass", back_populates="ticket", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Ticket(ticket_no={self.ticket_no}, passenger_id={self.passenger_id})>"


class TicketFlight(Base):
    """机票航班关联表"""
    __tablename__ = "ticket_flights"

    ticket_no = Column(String(20), ForeignKey("tickets.ticket_no"), primary_key=True)
    flight_id = Column(Integer, ForeignKey("flights.flight_id"), primary_key=True)
    fare_conditions = Column(String(20), comment="票价条件")
    amount = Column(Integer, comment="金额")

    ticket = relationship("Ticket", back_populates="ticket_flights")
    flight = relationship("Flight")

    def __repr__(self):
        return f"<TicketFlight(ticket_no={self.ticket_no}, flight_id={self.flight_id})>"


class BoardingPass(Base):
    """登机牌表"""
    __tablename__ = "boarding_passes"

    ticket_no = Column(String(20), ForeignKey("tickets.ticket_no"), primary_key=True)
    flight_id = Column(Integer, ForeignKey("flights.flight_id"), primary_key=True)
    boarding_no = Column(Integer, comment="登机口号")
    seat_no = Column(String(10), comment="座位号")

    ticket = relationship("Ticket", back_populates="boarding_passes")
    flight = relationship("Flight")

    def __repr__(self):
        return f"<BoardingPass(ticket_no={self.ticket_no}, flight_id={self.flight_id}, seat_no={self.seat_no})>"
