"""酒店数据模型"""
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

# 从 flight_models 导入 Base
from .flight_models import Base


class Hotel(Base):
    """酒店表"""
    __tablename__ = "hotels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(300), comment="酒店名称")
    location: Mapped[str] = mapped_column(String(200), comment="位置")
    price_tier: Mapped[str] = mapped_column(String(50), comment="价格档次")
    checkin_date: Mapped[str] = mapped_column(String(50), comment="入住日期")
    checkout_date: Mapped[str] = mapped_column(String(50), comment="退房日期")
    booked: Mapped[int] = mapped_column(Integer, default=0, comment="是否已预订")

    def __repr__(self):
        return f"<Hotel(id={self.id}, name={self.name}, location={self.location})>"
