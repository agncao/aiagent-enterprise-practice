"""车租赁工具"""
from typing import Annotated

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from app.dao.repositories.car_rental_repository import CarRentalRepository
from .location_trans import transform_location


class CarRentalSearchInput(BaseModel):
    """车租赁搜索参数"""
    location: Annotated[str | None, Field(description="汽车租赁的位置")] = None
    name: Annotated[str | None, Field(description="汽车租赁公司的名称")] = None


@tool(args_schema=CarRentalSearchInput)
def search_car_rentals(
    location: str | None = None,
    name: str | None = None,
) -> list[dict]:
    """
    根据位置、名称、价格层级、开始日期和结束日期搜索汽车租赁信息。

    参数:
    - location (Optional[str]): 汽车租赁的位置。默认为None。
    - name (Optional[str]): 汽车租赁公司的名称。默认为None。
    返回:
    - list[dict]: 包含匹配搜索条件的汽车租赁信息的字典列表。
    """
    repo = CarRentalRepository()
    location = transform_location(location)
    rentals = repo.search_car_rentals(
        location=location,
        name=name,
        limit=20,
    )

    if not rentals:
        return []

    return [rental.to_dict() for rental in rentals]


class CarRentalBookInput(BaseModel):
    """租车预订参数"""
    rental_id: Annotated[int, Field(description="要预订的汽车租赁服务的ID。")]


@tool(args_schema=CarRentalBookInput)
def book_car_rental(rental_id: int) -> str:
    """
    通过ID预订汽车租赁服务。

    返回:
    - str: 表明汽车租赁是否成功预订的消息。
    """

    repo = CarRentalRepository()
    success = repo.book_car_rental(rental_id)
    if success:
        return f"租车服务 {rental_id} 预订成功。"
    return f"未找到ID为 {rental_id} 的租车服务。"

class UpdateCarRentalDatesInput(BaseModel):
    """更新租车日期参数"""
    rental_id: Annotated[int, Field(description="要更新日期的汽车租赁服务的ID。")]
    start_date: Annotated[str | None, Field(description="汽车租赁的新开始日期。")] = None
    end_date: Annotated[str | None, Field(description="汽车租赁的新结束日期。")] = None

@tool(args_schema=UpdateCarRentalDatesInput)
def update_car_rental_dates(
    rental_id: int,
    start_date: str | None = None,
    end_date: str | None = None,
) -> str:
    """
    根据ID更新汽车租赁的开始和结束日期。

    返回:
    - str: 表明汽车租赁日期是否成功更新的消息。
    """
    repo = CarRentalRepository()
    success = repo.update_car_rental_dates(
        rental_id,
        start_date=start_date,
        end_date=end_date,
    )
    if success:
        return f"租车服务 {rental_id} 成功更新。"
    return f"未找到ID为 {rental_id} 的租车服务。"

@tool(args_schema=CarRentalBookInput)
def cancel_car_rental(rental_id: int) -> str:
    """
    根据ID取消汽车租赁服务。

    参数:
        rental_id (int): 要取消的汽车租赁服务的ID。

    返回:
        str: 表明汽车租赁是否成功取消的消息。
    """
    repo = CarRentalRepository()
    success = repo.cancel_car_rental(rental_id)
    if success:
        return f"租车服务 {rental_id} 预订已取消。"
    return f"未找到ID为 {rental_id} 的租车服务。"
