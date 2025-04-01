"""
酒店仓储模块 - 提供酒店相关的数据访问功能
"""
from datetime import date, datetime
from typing import Optional, Union, List, Dict

from sqlalchemy import or_

from infrastructure.connection.db_manager import DatabaseManager
from repository.models.hotels import Hotel
from app.tools.location_trans import transform_location

class HotelRepository:
    """酒店仓储类，提供酒店相关的数据访问方法"""
    
    @staticmethod
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
        session = DatabaseManager.get_session()
        try:
            # 构建查询
            query = session.query(Hotel)
            
            # 添加过滤条件
            if location:
                transformed_location = transform_location(location)
                query = query.filter(Hotel.location.like(f"%{transformed_location}%"))
            
            if name:
                query = query.filter(Hotel.name.like(f"%{name}%"))
            
            # 执行查询
            hotels = query.all()
            
            # 转换为字典列表
            results = []
            for hotel in hotels:
                hotel_dict = {
                    "id": hotel.id,
                    "name": hotel.name,
                    "location": hotel.location,
                    "price": hotel.price,
                    "rating": hotel.rating,
                    "booked": hotel.booked,
                    "checkin_date": hotel.checkin_date,
                    "checkout_date": hotel.checkout_date
                }
                results.append(hotel_dict)
            
            print('查询酒店的结果: ', results)
            return results
        finally:
            DatabaseManager.close_session(session)

    @staticmethod
    def book_hotel(hotel_id: int) -> str:
        """
        通过ID预订酒店。

        参数:
            hotel_id (int): 要预订的酒店的ID。

        返回:
            str: 表明酒店是否成功预订的消息。
        """
        session = DatabaseManager.get_session()
        try:
            # 查询酒店
            hotel = session.query(Hotel).filter(Hotel.id == hotel_id).first()
            
            if not hotel:
                return f"未找到ID为 {hotel_id} 的酒店。"
            
            # 更新预订状态
            hotel.booked = 1
            session.commit()
            
            return f"Hotel {hotel_id} 成功预定。"
        except Exception as e:
            session.rollback()
            return f"预订酒店时发生错误: {str(e)}"
        finally:
            DatabaseManager.close_session(session)

    @staticmethod
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
        session = DatabaseManager.get_session()
        try:
            # 查询酒店
            hotel = session.query(Hotel).filter(Hotel.id == hotel_id).first()
            
            if not hotel:
                return f"未找到ID为 {hotel_id} 的酒店。"
            
            # 更新入住和退房日期
            if checkin_date:
                hotel.checkin_date = checkin_date
            
            if checkout_date:
                hotel.checkout_date = checkout_date
            
            session.commit()
            
            return f"Hotel {hotel_id} 成功更新。"
        except Exception as e:
            session.rollback()
            return f"更新酒店预订时发生错误: {str(e)}"
        finally:
            DatabaseManager.close_session(session)

    @staticmethod
    def cancel_hotel(hotel_id: int) -> str:
        """
        根据ID取消酒店预订。

        参数:
            hotel_id (int): 要取消的酒店预订的ID。

        返回:
            str: 表明酒店预订是否成功取消的消息。
        """
        session = DatabaseManager.get_session()
        try:
            # 查询酒店
            hotel = session.query(Hotel).filter(Hotel.id == hotel_id).first()
            
            if not hotel:
                return f"未找到ID为 {hotel_id} 的酒店。"
            
            # 将booked字段设置为0来表示取消预订
            hotel.booked = 0
            session.commit()
            
            return f"Hotel {hotel_id} 成功取消。"
        except Exception as e:
            session.rollback()
            return f"取消酒店预订时发生错误: {str(e)}"
        finally:
            DatabaseManager.close_session(session)