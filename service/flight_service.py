"""
航班服务模块 - 提供航班和机票相关的业务逻辑
"""
from datetime import date, datetime
from typing import Optional, List, Dict
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool

from repository.flights_repository import FlightRepository

class FlightService:
    """航班服务类，提供航班和机票相关的业务功能"""
    
    @staticmethod
    @tool
    def fetch_user_flight_information(config: RunnableConfig) -> List[Dict]:
        """
        此函数通过给定的乘客ID，从数据库中获取该乘客的所有机票信息及其相关联的航班信息和座位分配情况。
        返回:
            包含每张机票的详情、关联航班的信息及座位分配的字典列表。
        """
        return FlightRepository.fetch_user_flight_information(config)

    @staticmethod
    @tool
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
        return FlightRepository.search_flights(
            departure_airport, arrival_airport, start_time, end_time, limit
        )

    @staticmethod
    @tool
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
        return FlightRepository.update_ticket_to_new_flight(ticket_no, new_flight_id, config=config)

    @staticmethod
    @tool
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
        return FlightRepository.cancel_ticket(ticket_no, config=config)