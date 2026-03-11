"""航班数据仓储"""
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from app.dao.base_repository import BaseRepository
from app.dao.models.booking_models import BoardingPass, Ticket, TicketFlight
from app.dao.models.flight_models import AirportData, Flight
from app.dao.session import get_session

class FlightRepository(BaseRepository[Flight]):
    """航班数据仓储"""

    def __init__(self) -> None:
        super().__init__(Flight)

    def search_flights(
        self,
        departure_airport: str | None = None,
        arrival_airport: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        limit: int = 20,
    ) -> list[Flight]:
        """搜索航班"""

        with get_session() as session:
            query = session.query(Flight)

            if departure_airport:
                query = query.filter(Flight.departure_airport == departure_airport)

            if arrival_airport:
                query = query.filter(Flight.arrival_airport == arrival_airport)

            if start_time:
                query = query.filter(Flight.scheduled_departure >= start_time)

            if end_time:
                query = query.filter(Flight.scheduled_departure <= end_time)

            return query.limit(limit).all()

    def get_by_flight_no(self, flight_no: str) -> Flight | None:
        """根据航班号查询航班"""
        return self.get_by(flight_no=flight_no)

    def get_by_airports(self, departure: str, arrival: str, limit: int = 50) -> list[Flight]:
        """查询指定起降机场的航班"""
        

        with get_session() as session:
            return session.query(Flight).filter(
                Flight.departure_airport == departure,
                Flight.arrival_airport == arrival,
            ).limit(limit).all()

    def get_by_status(self, status: str, limit: int = 50) -> list[Flight]:
        """根据状态查询航班"""
        return self.list(limit=limit, status=status)


class AirportRepository(BaseRepository[AirportData]):
    """机场数据仓储"""

    def __init__(self) -> None:
        super().__init__(AirportData)

    def get_by_code(self, airport_code: str) -> AirportData | None:
        """根据机场代码查询"""
        return self.get_by(airport_code=airport_code)

    def search_by_city(self, city: str) -> list[AirportData]:
        """根据城市查询机场"""
        return self.list(limit=100, city=city)

    def search_by_name(self, keyword: str) -> list[AirportData]:
        """根据机场名称搜索"""
        

        with get_session() as session:
            return session.query(AirportData).filter(
                AirportData.airport_name.like(f"%{keyword}%")
            ).all()


class TicketRepository(BaseRepository[Ticket]):
    """机票数据仓储"""

    def __init__(self) -> None:
        super().__init__(Ticket)

    def fetch_user_flight_information(self, passenger_id: str) -> list[dict[str, Any]]:
        """根据乘客ID获取所有机票信息及其相关联的航班信息和座位分配情况

        Args:
            passenger_id: 乘客ID

        Returns:
            包含每张机票的详情、关联航班的信息及座位分配的字典列表
        """
        

        with get_session() as session:
            query = session.query(
                Ticket.ticket_no,
                Ticket.book_ref,
                Flight.flight_id,
                Flight.flight_no,
                Flight.departure_airport,
                Flight.arrival_airport,
                Flight.scheduled_departure,
                Flight.scheduled_arrival,
                BoardingPass.seat_no,
                TicketFlight.fare_conditions,
            ).join(
                TicketFlight, Ticket.ticket_no == TicketFlight.ticket_no
            ).join(
                Flight, TicketFlight.flight_id == Flight.flight_id
            ).join(
                BoardingPass,
                (BoardingPass.ticket_no == Ticket.ticket_no) &
                (BoardingPass.flight_id == Flight.flight_id)
            ).filter(
                Ticket.passenger_id == passenger_id
            )

            results = []
            for row in query.all():
                results.append({
                    "ticket_no": row.ticket_no,
                    "book_ref": row.book_ref,
                    "flight_id": row.flight_id,
                    "flight_no": row.flight_no,
                    "departure_airport": row.departure_airport,
                    "arrival_airport": row.arrival_airport,
                    "scheduled_departure": row.scheduled_departure,
                    "scheduled_arrival": row.scheduled_arrival,
                    "seat_no": row.seat_no,
                    "fare_conditions": row.fare_conditions,
                })
            return results

    def get_by_passenger(self, passenger_id: str) -> list[Ticket]:
        """根据乘客ID查询所有机票"""
        return self.list(limit=1000, passenger_id=passenger_id)

    def get_by_booking(self, book_ref: str) -> list[Ticket]:
        """根据预订编号查询机票"""
        return self.list(limit=100, book_ref=book_ref)

    def get_ticket_flights(self, ticket_no: str) -> list[dict]:
        """获取机票关联的航班信息"""
        

        with get_session() as session:
            query = session.query(
                Ticket, Flight, TicketFlight, BoardingPass
            ).join(
                TicketFlight, Ticket.ticket_no == TicketFlight.ticket_no
            ).join(
                Flight, TicketFlight.flight_id == Flight.flight_id
            ).outerjoin(
                BoardingPass,
                (BoardingPass.ticket_no == Ticket.ticket_no) &
                (BoardingPass.flight_id == Flight.flight_id)
            ).filter(
                Ticket.ticket_no == ticket_no
            )

            results = []
            for ticket, flight, tf, bp in query.all():
                results.append({
                    "ticket_no": ticket.ticket_no,
                    "passenger_id": ticket.passenger_id,
                    "flight_id": flight.flight_id,
                    "flight_no": flight.flight_no,
                    "departure_airport": flight.departure_airport,
                    "arrival_airport": flight.arrival_airport,
                    "scheduled_departure": flight.scheduled_departure,
                    "scheduled_arrival": flight.scheduled_arrival,
                    "fare_conditions": tf.fare_conditions,
                    "amount": tf.amount,
                    "seat_no": bp.seat_no if bp else None,
                })
            return results

    def update_ticket_flight(self, ticket_no: str, new_flight_id: int) -> bool:
        """更新机票的航班（简单版本，无验证）"""
        

        with get_session() as session:
            result = session.query(TicketFlight).filter(
                TicketFlight.ticket_no == ticket_no
            ).first()

            if result:
                result.flight_id = new_flight_id
                session.commit()
                return True
            return False

    def update_ticket_to_new_flight(
        self,
        ticket_no: str,
        new_flight_id: int,
        passenger_id: str | None = None,
        min_hours_before_departure: int = 3,
    ) -> tuple[bool, str]:
        """将用户的机票更新为新的有效航班

        步骤：
        1. 查询新航班详情
        2. 时间验证：确保新选择的航班起飞时间与当前时间相差不少于指定小时数
        3. 确认原机票存在性
        4. 验证乘客身份（如果提供了passenger_id）
        5. 更新机票对应的航班ID

        Args:
            ticket_no: 要更新的机票编号
            new_flight_id: 新的航班ID
            passenger_id: 乘客ID（用于验证，可选）
            min_hours_before_departure: 起飞前最少小时数，默认3小时

        Returns:
            (是否成功, 消息)
        """
        

        with get_session() as session:
            # 1. 查询新航班的信息
            new_flight = session.query(Flight).filter(
                Flight.flight_id == new_flight_id
            ).first()

            if not new_flight:
                return False, f"提供的新的航班ID {new_flight_id} 无效。"

            # 2. 时间验证：确保新航班起飞时间与当前时间相差不少于3小时
            timezone = ZoneInfo("Etc/GMT-3")
            current_time = datetime.now(tz=timezone)
            departure_time = new_flight.scheduled_departure

            if departure_time:
                # 如果 departure_time 是 naive datetime，假设它使用同样的时区
                if departure_time.tzinfo is None:
                    departure_time = departure_time.replace(tzinfo=timezone)

                time_until = (departure_time - current_time).total_seconds()
                min_seconds = min_hours_before_departure * 3600

                if time_until < min_seconds:
                    return False, (
                        f"不允许重新安排到距离当前时间少于 {min_hours_before_departure} 小时的航班。"
                        f"所选航班时间为 {departure_time}。"
                    )

            # 3. 确认原机票的存在性
            current_ticket_flight = session.query(TicketFlight).filter(
                TicketFlight.ticket_no == ticket_no
            ).first()

            if not current_ticket_flight:
                return False, f"未找到给定机票号码 {ticket_no} 的现有机票。"

            # 4. 确认已登录用户确实拥有此机票
            if passenger_id:
                ticket = session.query(Ticket).filter(
                    Ticket.ticket_no == ticket_no,
                    Ticket.passenger_id == passenger_id,
                ).first()

                if not ticket:
                    return False, f"当前登录的乘客ID为 {passenger_id}，不是机票 {ticket_no} 的拥有者。"

            # 5. 更新机票对应的航班ID
            current_ticket_flight.flight_id = new_flight_id
            session.commit()

            return True, f"机票 {ticket_no} 已成功更新为新的航班 {new_flight.flight_no}。"

    def cancel_ticket(self, ticket_no: str) -> bool:
        """取消机票"""
        

        with get_session() as session:
            # 删除机票航班关联
            session.query(TicketFlight).filter(
                TicketFlight.ticket_no == ticket_no
            ).delete()
            # 删除登机牌
            session.query(BoardingPass).filter(
                BoardingPass.ticket_no == ticket_no
            ).delete()
            # 删除机票
            session.query(Ticket).filter(
                Ticket.ticket_no == ticket_no
            ).delete()
            session.commit()
            return True

if __name__ == '__main__':
    flight_repo = FlightRepository()
    available_flights = flight_repo.search_flights(departure_airport="SEZ", arrival_airport="SHA")
    for flight in available_flights:
        print(flight)
    ticket_repo = TicketRepository()
    tickets = ticket_repo.fetch_user_flight_information(passenger_id="3461 215546")
    for ticket in tickets:
        print(ticket)
