"""
酒店服务模块 - 提供酒店相关的业务逻辑
"""
from datetime import date, datetime
from typing import Optional, Union, List, Dict

from langchain_core.tools import tool

from repository.hotels_repository import HotelRepository

class HotelService:
    """酒店服务类，提供酒店相关的业务功能"""
    
    @staticmethod
    @tool
    def search_hotels(
            location: Optional[str] = None,
            name: Optional[str] = None
            # price_tier: Optional[str] = None,
            # checkin_date: Optional[Union[datetime, date]] = None,
            # checkout_date: Optional[Union[datetime, date]] = None,
    ) -> List[Dict]:
        """
        根据位置、名称、价格层级、入住日期和退房日期搜索酒店。

        参数:
            location (Optional[str]): 酒店的位置。默认为None。
            name (Optional[str]): 酒店的名称。默认为None。

        返回:
            List[Dict]: 包含匹配搜索条件的酒店信息的字典列表。
        """
        return HotelRepository.search_hotels(location, name)

    @staticmethod
    @tool
    def book_hotel(hotel_id: int) -> str:
        """
        通过ID预订酒店。

        参数:
            hotel_id (int): 要预订的酒店的ID。

        返回:
            str: 表明酒店是否成功预订的消息。
        """
        return HotelRepository.book_hotel(hotel_id)

    @staticmethod
    @tool
    def update_hotel(
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
        return HotelRepository.update_hotel(hotel_id, checkin_date, checkout_date)

    @staticmethod
    @tool
    def cancel_hotel(hotel_id: int) -> str:
        """
        根据ID取消酒店预订。

        参数:
            hotel_id (int): 要取消的酒店预订的ID。

        返回:
            str: 表明酒店预订是否成功取消的消息。
        """
        return HotelRepository.cancel_hotel(hotel_id)