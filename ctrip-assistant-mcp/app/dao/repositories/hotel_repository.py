"""酒店数据仓储"""


from app.dao.base_repository import BaseRepository
from app.dao.models.hotel_models import Hotel


class HotelRepository(BaseRepository[Hotel]):
    """酒店数据仓储"""

    def __init__(self):
        super().__init__(Hotel)

    def search_hotels(
        self,
        location: str | None = None,
        name: str | None = None,
        price_tier: str | None = None,
        booked: int | None = None,
        limit: int = 50,
    ) -> list[Hotel]:
        """搜索酒店"""
        from app.dao.session import get_session 

        with get_session() as session:
            query = session.query(Hotel)

            if location:
                query = query.filter(Hotel.location.like(f"%{location}%"))

            if name:
                query = query.filter(Hotel.name.like(f"%{name}%"))

            if price_tier:
                query = query.filter(Hotel.price_tier == price_tier)

            if booked is not None:
                query = query.filter(Hotel.booked == booked)

            return query.limit(limit).all()

    def book_hotel(self, hotel_id: int) -> bool:
        """预订酒店"""
        from app.dao.session import get_session 

        with get_session() as session:
            hotel = session.query(Hotel).filter(Hotel.id == hotel_id).first()
            if hotel:
                hotel.booked = 1
                session.commit()
                return True
            return False

    def cancel_hotel(self, hotel_id: int) -> bool:
        """取消酒店预订"""
        from app.dao.session import get_session 

        with get_session() as session:
            hotel = session.query(Hotel).filter(Hotel.id == hotel_id).first()
            if hotel:
                hotel.booked = 0
                session.commit()
                return True
            return False

    def update_hotel_dates(
        self,
        hotel_id: int,
        checkin_date: str | None = None,
        checkout_date: str | None = None,
    ) -> bool:
        """更新酒店入住日期"""
        from app.dao.session import get_session

        with get_session() as session:
            hotel = session.query(Hotel).filter(Hotel.id == hotel_id).first()
            if hotel:
                if checkin_date:
                    hotel.checkin_date = checkin_date
                if checkout_date:
                    hotel.checkout_date = checkout_date
                session.commit()
                return True
            return False

    def get_by_location(self, location: str, limit: int = 50) -> list[Hotel]:
        """根据位置查询酒店"""
        return self.search_hotels(location=location, limit=limit)

    def get_available(self, limit: int = 50) -> list[Hotel]:
        """获取可预订的酒店"""
        return self.search_hotels(booked=0, limit=limit)

if __name__ == '__main__':
    hotel_repo = HotelRepository()
    available_hotels = hotel_repo.search_hotels(booked=0, price_tier="Midscale")
    for hotel in available_hotels:
        print(hotel)
