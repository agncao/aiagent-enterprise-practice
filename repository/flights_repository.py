"""
航班仓储模块 - 提供航班和机票相关的数据访问功能
"""
from datetime import date, datetime
from typing import Optional, List, Dict
import os
import pytz
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from langchain_core.runnables import RunnableConfig

from infrastructure.connection.db_manager import DatabaseManager
from repository.models.flights import Flight
from repository.models.tickets import Ticket
from repository.models.ticket_flights import TicketFlight
from repository.models.boarding_passes import BoardingPass

class FlightRepository:
    """航班仓储类，提供航班和机票相关的数据访问方法"""
    
    @staticmethod
    def fetch_user_flight_information(config: RunnableConfig) -> List[Dict]:
        """
        此函数通过给定的乘客ID，从数据库中获取该乘客的所有机票信息及其相关联的航班信息和座位分配情况。
        返回:
            包含每张机票的详情、关联航班的信息及座位分配的字典列表。
        """
        configuration = config.get("configurable", {})
        passenger_id = configuration.get("passenger_id", None)
        if not passenger_id:
            raise ValueError("未配置乘客 ID。")

        session = DatabaseManager.get_session()
        try:
            # 使用SQLAlchemy查询
            results = (
                session.query(
                    Ticket, Flight, BoardingPass, TicketFlight
                )
                .join(TicketFlight, Ticket.ticket_no == TicketFlight.ticket_no)
                .join(Flight, TicketFlight.flight_id == Flight.flight_id)
                .join(
                    BoardingPass, 
                    and_(
                        BoardingPass.ticket_no == Ticket.ticket_no,
                        BoardingPass.flight_id == Flight.flight_id
                    )
                )
                .filter(Ticket.passenger_id == passenger_id)
                .all()
            )
            
            # 转换结果为字典列表
            flight_info = []
            for ticket, flight, boarding_pass, ticket_flight in results:
                flight_info.append({
                    "ticket_no": ticket.ticket_no,
                    "book_ref": ticket.book_ref,
                    "flight_id": flight.flight_id,
                    "flight_no": flight.flight_no,
                    "departure_airport": flight.departure_airport,
                    "arrival_airport": flight.arrival_airport,
                    "scheduled_departure": flight.scheduled_departure,
                    "scheduled_arrival": flight.scheduled_arrival,
                    "seat_no": boarding_pass.seat_no,
                    "fare_conditions": ticket_flight.fare_conditions
                })
            
            return flight_info
        finally:
            DatabaseManager.close_session(session)

    @staticmethod
    def search_flights(
            departure_airport: Optional[str] = None,
            arrival_airport: Optional[str] = None,
            start_time: Optional[date | datetime] = None,
            end_time: Optional[date | datetime] = None,
            limit: int = 20,
    ) -> List[Dict]:
        """
        根据指定的参数（如出发机场、到达机场、出发时间范围等）搜索航班，并返回匹配的航班列表。
        可以设置一个限制值来控制返回的结果数量。

        参数:
        - departure_airport (Optional[str]): 出发机场（可选）。
        - arrival_airport (Optional[str]): 到达机场（可选）。
        - start_time (Optional[date | datetime]): 出发时间范围的开始时间（可选）。
        - end_time (Optional[date | datetime]): 出发时间范围的结束时间（可选）。
        - limit (int): 返回结果的最大数量，默认为20。

        返回:
            匹配条件的航班信息列表。
        """
        session = DatabaseManager.get_session()
        try:
            # 构建查询
            query = session.query(Flight)
            
            # 添加过滤条件
            if departure_airport:
                query = query.filter(Flight.departure_airport == departure_airport)
            
            if arrival_airport:
                query = query.filter(Flight.arrival_airport == arrival_airport)
            
            if start_time:
                query = query.filter(Flight.scheduled_departure >= start_time)
            
            if end_time:
                query = query.filter(Flight.scheduled_departure <= end_time)
            
            # 限制结果数量
            query = query.limit(limit)
            
            # 执行查询
            flights = query.all()
            
            # 转换为字典列表
            results = []
            for flight in flights:
                flight_dict = {
                    "flight_id": flight.flight_id,
                    "flight_no": flight.flight_no,
                    "departure_airport": flight.departure_airport,
                    "arrival_airport": flight.arrival_airport,
                    "scheduled_departure": flight.scheduled_departure,
                    "scheduled_arrival": flight.scheduled_arrival,
                    "status": flight.status,
                    "aircraft_code": flight.aircraft_code,
                    "actual_departure": flight.actual_departure,
                    "actual_arrival": flight.actual_arrival
                }
                results.append(flight_dict)
            
            return results
        finally:
            DatabaseManager.close_session(session)

    @staticmethod
    def update_ticket_to_new_flight(
            ticket_no: str, new_flight_id: int, *, config: RunnableConfig
    ) -> str:
        """
        将用户的机票更新为新的有效航班。步骤如下：
        1、检查乘客ID：首先从传入的配置中获取乘客ID，并验证其是否存在。
        2、查询新航班详情：根据提供的新航班ID查询航班详情，包括出发机场、到达机场和计划起飞时间。
        3、时间验证：确保新选择的航班起飞时间与当前时间相差不少于3小时。
        4、确认原机票存在性：验证提供的机票号是否存在于系统中。
        5、验证乘客身份：确保请求修改机票的乘客是该机票的实际拥有者。
        6、更新机票信息：如果所有检查都通过，则更新机票对应的新航班ID，并提交更改。

        参数:
        - ticket_no (str): 要更新的机票编号。
        - new_flight_id (int): 新的航班ID。
        - config (RunnableConfig): 配置信息，包含乘客ID等必要参数。

        返回:
        - str: 操作结果的消息。
        """
        configuration = config.get("configurable", {})
        passenger_id = configuration.get("passenger_id", None)
        if not passenger_id:
            raise ValueError("未配置乘客 ID。")

        session = DatabaseManager.get_session()
        try:
            # 查询新航班的信息
            new_flight = session.query(Flight).filter(Flight.flight_id == new_flight_id).first()
            if not new_flight:
                return "提供的新的航班 ID 无效。"
            
            # 设置时区并计算当前时间和新航班起飞时间之间的差值
            timezone = pytz.timezone("Etc/GMT-3")
            current_time = datetime.now(tz=timezone)
            
            # 假设scheduled_departure是字符串格式，需要转换为datetime对象
            if isinstance(new_flight.scheduled_departure, str):
                departure_time = datetime.strptime(
                    new_flight.scheduled_departure, "%Y-%m-%d %H:%M:%S.%f%z"
                )
            else:
                departure_time = new_flight.scheduled_departure
                
            time_until = (departure_time - current_time).total_seconds()
            if time_until < (3 * 3600):
                return f"不允许重新安排到距离当前时间少于 3 小时的航班。所选航班时间为 {departure_time}。"

            # 确认原机票的存在性
            ticket_flight = session.query(TicketFlight).filter(
                TicketFlight.ticket_no == ticket_no
            ).first()
            if not ticket_flight:
                return "未找到给定机票号码的现有机票。"

            # 确认已登录用户确实拥有此机票
            ticket = session.query(Ticket).filter(
                Ticket.ticket_no == ticket_no,
                Ticket.passenger_id == passenger_id
            ).first()
            if not ticket:
                return f"当前登录的乘客 ID 为 {passenger_id}，不是机票 {ticket_no} 的拥有者。"

            # 更新机票对应的航班ID
            ticket_flight.flight_id = new_flight_id
            session.commit()
            
            return "机票已成功更新为新的航班。"
        except Exception as e:
            session.rollback()
            return f"更新机票时发生错误: {str(e)}"
        finally:
            DatabaseManager.close_session(session)

    @staticmethod
    def cancel_ticket(ticket_no: str, *, config: RunnableConfig) -> str:
        """
        取消用户的机票并将其从数据库中删除。步骤如下：
        1、检查乘客ID：首先从传入的配置中获取乘客ID，并验证其是否存在。
        2、查询机票存在性：根据提供的机票号查询该机票是否存在于系统中。
        3、验证乘客身份：确保请求取消机票的乘客是该机票的实际拥有者。
        4、删除机票信息：如果所有检查都通过，则从数据库中删除该机票的信息，并提交更改。

        参数:
        - ticket_no (str): 要取消的机票编号。
        - config (RunnableConfig): 配置信息，包含乘客ID等必要参数。

        返回:
        - str: 操作结果的消息。
        """
        configuration = config.get("configurable", {})
        passenger_id = configuration.get("passenger_id", None)
        if not passenger_id:
            raise ValueError("未配置乘客 ID。")

        session = DatabaseManager.get_session()
        try:
            # 查询给定机票号是否存在
            ticket_flight = session.query(TicketFlight).filter(
                TicketFlight.ticket_no == ticket_no
            ).first()
            if not ticket_flight:
                return "未找到给定机票号码的现有机票。"

            # 确认已登录用户确实拥有此机票
            ticket = session.query(Ticket).filter(
                Ticket.ticket_no == ticket_no,
                Ticket.passenger_id == passenger_id
            ).first()
            if not ticket:
                return f"当前登录的乘客 ID 为 {passenger_id}，不是机票 {ticket_no} 的拥有者。"

            # 删除机票对应的记录
            session.delete(ticket_flight)
            session.commit()
            
            return "机票已成功取消。"
        except Exception as e:
            session.rollback()
            return f"取消机票时发生错误: {str(e)}"
        finally:
            DatabaseManager.close_session(session)
