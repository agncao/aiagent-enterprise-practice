"""旅行推荐数据仓储"""

from app.dao.base_repository import BaseRepository
from app.dao.models.trip_models import TripRecommendation


class TripRecommendationRepository(BaseRepository[TripRecommendation]):
    """旅行推荐数据仓储"""

    def __init__(self):
        super().__init__(TripRecommendation)

    def search_trip_recommendations(
        self,
        location: str | None = None,
        name: str | None = None,
        keywords: str | None = None,
        booked: int | None = None,
        limit: int = 50,
    ) -> list[TripRecommendation]:
        """搜索旅行推荐"""
        from app.dao.session import get_session

        with get_session() as session:
            query = session.query(TripRecommendation)

            if location:
                query = query.filter(TripRecommendation.location.like(f"%{location}%"))

            if name:
                query = query.filter(TripRecommendation.name.like(f"%{name}%"))

            if keywords:
                # 支持逗号分隔的多个关键词
                keyword_list = [k.strip() for k in keywords.split(",")]
                conditions = [TripRecommendation.keywords.like(f"%{k}%") for k in keyword_list]
                from sqlalchemy import or_
                query = query.filter(or_(*conditions))

            if booked is not None:
                query = query.filter(TripRecommendation.booked == booked)

            return query.limit(limit).all()

    def book_excursion(self, recommendation_id: int) -> bool:
        """预订旅行项目"""
        from app.dao.session import get_session

        with get_session() as session:
            trip = session.query(TripRecommendation).filter(
                TripRecommendation.id == recommendation_id
            ).first()
            if trip:
                trip.booked = 1
                session.commit()
                return True
            return False

    def cancel_excursion(self, recommendation_id: int) -> bool:
        """取消旅行项目"""
        from app.dao.session import get_session

        with get_session() as session:
            trip = session.query(TripRecommendation).filter(
                TripRecommendation.id == recommendation_id
            ).first()
            if trip:
                trip.booked = 0
                session.commit()
                return True
            return False

    def update_excursion_details(self, recommendation_id: int, details: str) -> bool:
        """更新旅行项目详情"""
        from app.dao.session import get_session

        with get_session() as session:
            trip = session.query(TripRecommendation).filter(
                TripRecommendation.id == recommendation_id
            ).first()
            if trip:
                trip.details = details
                session.commit()
                return True
            return False

    def get_by_location(self, location: str, limit: int = 50) -> list[TripRecommendation]:
        """根据位置查询旅行推荐"""
        from app.dao.session import get_session

        with get_session() as session:
            return self.search_trip_recommendations(location=location, limit=limit)


if __name__ == '__main__':
    trip_repo = TripRecommendationRepository()
    available_trips = trip_repo.get_by_location("Zurich")
    for trip in available_trips:
        print(trip)
