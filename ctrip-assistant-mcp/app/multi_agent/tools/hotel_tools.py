"""酒店查询工具"""
from typing import Optional, Union
from datetime import datetime, date

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from app.dao.repositories.hotel_repository import HotelRepository

from .location_trans import transform_location

@tool
def search_hotels(
        location: Optional[str] = None,
        name: Optional[str] = None,
        # price_tier: Optional[str] = None,
        # checkin_date: Optional[Union[datetime, date]] = None,
        # checkout_date: Optional[Union[datetime, date]] = None,
) -> list[dict]:
    """
    根据位置、名称、价格层级、入住日期和退房日期搜索酒店。

    参数:
        location (Optional[str]): 酒店的位置。默认为None。
        name (Optional[str]): 酒店的名称。默认为None。

    返回:
        list[dict]: 包含匹配搜索条件的酒店信息的字典列表。
    """
    location = transform_location(location)
    repo = HotelRepository()
    hotels = repo.search_hotels(
        location=location,
        name=name,
        limit=20,
    )
    if not hotels:
        return []
    return [h.to_dict() for h in hotels]


@tool
def book_hotel(hotel_id: int) -> str:
    """
    通过ID预订酒店。

    参数:
        hotel_id (int): 要预订的酒店的ID。

    返回:
        str: 表明酒店是否成功预订的消息。
    """
    repo = HotelRepository()
    success = repo.book_hotel(hotel_id)
    if success:
        return f"酒店 {hotel_id} 预订成功。"
    return f"未找到ID为 {hotel_id} 的酒店。"

@tool
def cancel_hotel(hotel_id: int) -> str:
    """
    根据ID取消酒店预订。

    参数:
        hotel_id (int): 要取消的酒店预订的ID。

    返回:
        str: 表明酒店预订是否成功取消的消息。
    """
    repo = HotelRepository()
    success = repo.cancel_hotel(hotel_id)
    if success:
        return f"酒店 {hotel_id} 预订已取消。"
    return f"未找到ID为 {hotel_id} 的酒店。"

@tool
def update_hotel_dates(
        hotel_id: int,
        checkin_date: Optional[Union[datetime, date]] = None,
        checkout_date: Optional[Union[datetime, date]] = None,
) -> str:
    """
    根据ID更新酒店预订的入住和退房日期。

    参数:
        hotel_id (int): 要更新的酒店预订的ID。
        checkin_date (Optional[Union[datetime, date]]): 酒店的新入住日期。默认为None。
        checkout_date (Optional[Union[datetime, date]]): 酒店的新退房日期。默认为None。

    返回:
        str: 表明酒店预订是否成功更新的消息。
    """
    repo = HotelRepository()
    success = repo.update_hotel_dates(hotel_id, checkin_date, checkout_date)
    if success:
        return f"酒店 {hotel_id} 预订已更新。"
    return f"未找到ID为 {hotel_id} 的酒店。"
