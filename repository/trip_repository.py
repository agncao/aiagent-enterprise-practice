"""
旅行推荐仓储模块 - 提供旅行推荐相关的数据访问功能
"""
from typing import Optional, List, Dict

from sqlalchemy import or_

from infrastructure.connection.db_manager import DatabaseManager
from repository.models.trip_recommendations import TripRecommendation
from app.tools.location_trans import transform_location

class TripRepository:
    """旅行推荐仓储类，提供旅行推荐相关的数据访问方法"""
    
    @staticmethod
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
        session = DatabaseManager().Session()
        try:
            # 构建查询
            query = session.query(TripRecommendation)
            
            # 添加过滤条件
            if location:
                transformed_location = transform_location(location)
                query = query.filter(TripRecommendation.location.like(f"%{transformed_location}%"))
            
            if name:
                query = query.filter(TripRecommendation.name.like(f"%{name}%"))
            
            if keywords:
                keyword_list = keywords.split(",")
                keyword_conditions = []
                for keyword in keyword_list:
                    keyword_conditions.append(TripRecommendation.keywords.like(f"%{keyword.strip()}%"))
                query = query.filter(or_(*keyword_conditions))
            
            # 执行查询
            recommendations = query.all()
            
            # 转换为字典列表
            results = []
            for recommendation in recommendations:
                recommendation_dict = {
                    "id": recommendation.id,
                    "name": recommendation.name,
                    "location": recommendation.location,
                    "details": recommendation.details,
                    "keywords": recommendation.keywords,
                    "price": recommendation.price,
                    "rating": recommendation.rating,
                    "booked": recommendation.booked
                }
                results.append(recommendation_dict)
            
            return results
        finally:
            session.close()

    @staticmethod
    def book_excursion(recommendation_id: int) -> str:
        """
        通过推荐ID预订一次旅行项目。

        参数:
            recommendation_id (int): 要预订的旅行推荐的ID。

        返回:
            str: 表明旅行推荐是否成功预订的消息。
        """

        session = DatabaseManager().Session()
        try:
            # 查询旅行推荐
            recommendation = session.query(TripRecommendation).filter(
                TripRecommendation.id == recommendation_id
            ).first()
            
            if not recommendation:
                return f"未找到与 ID 相关的旅行推荐信息。 {recommendation_id}."
            
            # 更新预订状态
            recommendation.booked = 1
            session.commit()
            
            return f"旅行推荐 {recommendation_id} 成功预定."
        except Exception as e:
            session.rollback()
            return f"预订旅行推荐时发生错误: {str(e)}"
        finally:
            session.close()

    @staticmethod
    def update_excursion(recommendation_id: int, details: str) -> str:
        """
        根据ID更新旅行推荐的详细信息。

        参数:
            recommendation_id (int): 要更新的旅行推荐的ID。
            details (str): 旅行推荐的新详细信息。

        返回:
            str: 表明旅行推荐是否成功更新的消息。
        """

        session = DatabaseManager().Session()
        try:
            # 查询旅行推荐
            recommendation = session.query(TripRecommendation).filter(
                TripRecommendation.id == recommendation_id
            ).first()
            
            if not recommendation:
                return f"未找到ID为 {recommendation_id} 的旅行推荐。"
            
            # 更新详细信息
            recommendation.details = details
            session.commit()
            
            return f"旅行推荐 {recommendation_id} 成功更新。"
        except Exception as e:
            session.rollback()
            return f"更新旅行推荐时发生错误: {str(e)}"
        finally:
            session.close()

    @staticmethod
    def cancel_excursion(recommendation_id: int) -> str:
        """
        根据ID取消旅行推荐。

        参数:
            recommendation_id (int): 要取消的旅行推荐的ID。

        返回:
            str: 表明旅行推荐是否成功取消的消息。
        """

        session = DatabaseManager().Session()
        try:
            # 查询旅行推荐
            recommendation = session.query(TripRecommendation).filter(
                TripRecommendation.id == recommendation_id
            ).first()
            
            if not recommendation:
                return f"未找到ID为 {recommendation_id} 的旅行推荐。"
            
            # 将booked字段设置为0来表示取消预订
            recommendation.booked = 0
            session.commit()
            
            return f"旅行推荐 {recommendation_id} 成功取消。"
        except Exception as e:
            session.rollback()
            return f"取消旅行推荐时发生错误: {str(e)}"
        finally:
            session.close()
