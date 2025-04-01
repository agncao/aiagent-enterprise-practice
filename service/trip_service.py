"""
旅行推荐服务模块 - 提供旅行推荐相关的业务逻辑
"""
from typing import Optional, List, Dict

from langchain_core.tools import tool

from repository.trip_repository import TripRepository

class TripService:
    """旅行推荐服务类，提供旅行推荐相关的业务功能"""
    
    @staticmethod
    @tool
    def search_trip_recommendations(
            location: Optional[str] = None,
            name: Optional[str] = None,
            keywords: Optional[str] = None,
    ) -> List[Dict]:
        """
        根据位置、名称和关键词搜索旅行推荐。

        参数:
            location (Optional[str]): 旅行推荐的位置。默认为None。
            name (Optional[str]): 旅行推荐的名称。默认为None。
            keywords (Optional[str]): 关联到旅行推荐的关键词。默认为None。

        返回:
            List[Dict]: 包含匹配搜索条件的旅行推荐字典列表。
        """
        return TripRepository.search_trip_recommendations(location, name, keywords)

    @staticmethod
    @tool
    def book_excursion(recommendation_id: int) -> str:
        """
        通过推荐ID预订一次旅行项目。

        参数:
            recommendation_id (int): 要预订的旅行推荐的ID。

        返回:
            str: 表明旅行推荐是否成功预订的消息。
        """
        return TripRepository.book_excursion(recommendation_id)

    @staticmethod
    @tool
    def update_excursion(recommendation_id: int, details: str) -> str:
        """
        根据ID更新旅行推荐的详细信息。

        参数:
            recommendation_id (int): 要更新的旅行推荐的ID。
            details (str): 旅行推荐的新详细信息。

        返回:
            str: 表明旅行推荐是否成功更新的消息。
        """
        return TripRepository.update_excursion(recommendation_id, details)

    @staticmethod
    @tool
    def cancel_excursion(recommendation_id: int) -> str:
        """
        根据ID取消旅行推荐。

        参数:
            recommendation_id (int): 要取消的旅行推荐的ID。

        返回:
            str: 表明旅行推荐是否成功取消的消息。
        """
        return TripRepository.cancel_excursion(recommendation_id)