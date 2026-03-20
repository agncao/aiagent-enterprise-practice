"""旅行推荐工具"""
from typing import Annotated

from langchain_core.tools import tool
from app.dao.repositories.trip_recommendation_repository import TripRecommendationRepository
from .location_trans import transform_location


@tool
def search_trip_recommendations(
    location: str | None = None,
    name: str | None = None,
    keywords: str | None = None,
) -> list[dict]:
    """
    根据位置、名称和关键词搜索旅行推荐。

    参数:
        location: 旅行推荐的位置。默认为None。
        name: 旅行推荐的名称。默认为None。
        keywords: 关联到旅行推荐的关键词。默认为None。

    返回:
        list[dict]: 包含匹配搜索条件的旅行推荐字典列表。
    """
    location = transform_location(location)
    repo = TripRecommendationRepository()
    trips = repo.search_trip_recommendations(
        location=location,
        name=name,
        keywords=keywords
    )
    
    if not trips:
        return []
    
    return [trip.to_dict() for trip in trips]


@tool
def book_excursion(recommendation_id: int) -> str:
    """
    通过推荐ID预订一次旅行项目。

    参数:
        recommendation_id (int): 要预订的旅行推荐的ID。

    返回:
        str: 表明旅行推荐是否成功预订的消息。
    """
    repo = TripRecommendationRepository()
    success = repo.book_excursion(recommendation_id)
    if success:
        return f"旅行推荐 {recommendation_id} 预订成功。"
    return f"未找到ID为 {recommendation_id} 的旅行推荐。"

@tool
def cancel_excursion(recommendation_id: int) -> str:
    """
    根据ID取消旅行推荐。

    参数:
        recommendation_id (int): 要取消的旅行推荐的ID。

    返回:
        str: 表明旅行推荐是否成功取消的消息。
    """    
    repo = TripRecommendationRepository()
    success = repo.cancel_excursion(recommendation_id)
    if success:
        return f"旅行推荐 {recommendation_id} 预订已取消。"
    return f"未找到ID为 {recommendation_id} 的旅行推荐。"

@tool
def update_excursion_details(recommendation_id: int, details: str) -> str:
    """
    根据ID更新旅行推荐的详细信息。

    参数:
        recommendation_id (int): 要更新的旅行推荐的ID。
        details (str): 旅行推荐的新详细信息。

    返回:
        str: 表明旅行推荐是否成功更新的消息。
    """    
    repo = TripRecommendationRepository()
    success = repo.update_excursion_details(recommendation_id, details)
    if success:
        return f"旅行推荐 {recommendation_id} 已更新。"
    return f"未找到ID为 {recommendation_id} 的旅行推荐。"
