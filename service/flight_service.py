"""
航班服务模块 - 提供航班和机票相关的业务逻辑
"""
from typing import Optional, List, Dict
from langchain_core.runnables import RunnableConfig
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from langchain_core.tools import tool


from repository.flights_repository import FlightRepository


class FlightParams(BaseModel):
    departure_airport: str = Field(description="出发城市，例如：北京")
    arrival_airport: str = Field(description="抵达城市，例如：上海")
    departure_time: datetime = Field(description="出发日期和时间")
    arrival_time: Optional[datetime] = Field(default=None, description="抵达日期和时间，可选")
    limit: int = Field(default=20, description="返回结果数量限制")
    
    
    
def fetch_user_flight_information(config: RunnableConfig) -> List[Dict]:
    """
    此函数通过给定的乘客ID，从数据库中获取该乘客的所有机票信息及其相关联的航班信息和座位分配情况。
    返回:
        包含每张机票的详情、关联航班的信息及座位分配的字典列表。
    """
    return FlightRepository.fetch_user_flight_information(config)

@tool(args_schema = FlightParams)
def search_flights(departure_airport, arrival_airport, departure_time, arrival_time=None, limit: int = 20) -> List[Dict]:
    """
    根据指定的参数（如出发机场、到达机场、出发时间范围等）搜索航班，并返回匹配的航班列表。
    可以设置一个限制值来控制返回的结果数量。

    参数:
    - departure_airport: 出发机场
    - arrival_airport: 到达机场
    - departure_time: 出发时间
    - arrival_time: 到达时间
    - limit: 返回结果数量限制
    
    返回:
        匹配条件的航班信息列表。
    """
    arrival_time = arrival_time or departure_time
    return FlightRepository.search_flights(
        departure_airport, arrival_airport, departure_time, arrival_time, limit
    )

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