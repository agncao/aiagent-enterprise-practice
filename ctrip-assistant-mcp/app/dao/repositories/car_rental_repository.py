"""车租赁数据仓储"""

from app.dao.base_repository import BaseRepository
from app.dao.models.car_rental_models import CarRental


class CarRentalRepository(BaseRepository[CarRental]):
    """车租赁数据仓储"""

    def __init__(self):
        super().__init__(CarRental)

    def search_car_rentals(
        self,
        location: str | None = None,
        name: str | None = None,
        price_tier: str | None = None,
        booked: int | None = None,
        limit: int = 50,
    ) -> list[CarRental]:
        """
        根据位置、名称、价格层级搜索车租赁

        :param location: 汽车租赁的位置（模糊匹配）
        :param name: 汽车租赁公司的名称（模糊匹配）
        :param price_tier: 价格层级
        :param booked: 是否已预订
        :param limit: 返回结果的最大数量（默认50）
        :return: 符合条件的车租赁列表
        """
        from app.dao.session import get_session

        with get_session() as session:
            query = session.query(CarRental)

            if location:
                query = query.filter(CarRental.location.like(f"%{location}%"))

            if name:
                query = query.filter(CarRental.name.like(f"%{name}%"))

            if price_tier:
                query = query.filter(CarRental.price_tier == price_tier)

            if booked is not None:
                query = query.filter(CarRental.booked == booked)

            return query.limit(limit).all()

    def book_car_rental(self, rental_id: int) -> bool:
        """
        预订租车

        :param rental_id: 要预订的汽车租赁服务的ID。
        :return: 如果预订成功则返回True，否则返回False
        """
        from app.dao.session import get_session

        with get_session() as session:
            rental = session.query(CarRental).filter(CarRental.id == rental_id).first()
            if rental:
                rental.booked = 1
                session.commit()
                return True
            return False

    def cancel_car_rental(self, rental_id: int) -> bool:
        """
        根据ID取消汽车租赁服务。

        :param rental_id: 要取消的汽车租赁服务的ID。
        :return: 如果取消成功则返回True，否则返回False
        """
        from app.dao.session import get_session

        with get_session() as session:
            rental = session.query(CarRental).filter(CarRental.id == rental_id).first()
            if rental:
                rental.booked = 0
                session.commit()
                return True
            return False

    def update_car_rental_dates(
        self,
        rental_id: int,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> bool:
        """
        根据ID更新汽车租赁的开始和结束日期。

        :param rental_id: 要更新日期的汽车租赁服务的ID。
        :param start_date: 汽车租赁的新开始日期。
        :param end_date: 汽车租赁的新结束日期。
        :return: 如果更新成功则返回True，否则返回False
        """
        from app.dao.session import get_session

        with get_session() as session:
            rental = session.query(CarRental).filter(CarRental.id == rental_id).first()
            if rental:
                if start_date:
                    rental.start_date = start_date
                if end_date:
                    rental.end_date = end_date
                session.commit()
                return True
            return False

    def get_by_location(self, location: str, limit: int = 50) -> list[CarRental]:
        """根据位置查询租车"""
        return self.search_car_rentals(location=location, limit=limit)

    def get_available(self, limit: int = 50) -> list[CarRental]:
        """获取可预订的租车"""
        return self.search_car_rentals(booked=0, limit=limit)


if __name__ == '__main__':
    car_rental_repo = CarRentalRepository()
    available_rentals = car_rental_repo.get_available()
    for rental in available_rentals:
        print(rental)
