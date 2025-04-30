"""
工具的作用是发出指令
因为空间态势分析是基于Cesium的前端应用程序，所以工具的作用是发出指令，前端执行相应的操作。
这是写指令，例如发出添加实体、添加卫星、查询场景等指令。
"""
from typing import List, Optional, Dict, Any, TypedDict
from langchain_core.tools import tool
from agent.space.space_types import ScenarioConfig, EntityConfig, SatelliteTLEParams, Operation,get_yesterday_midnight_utc,get_today_midnight_utc
from infrastructure.logger import log
from langchain_core.runnables import RunnableConfig


# def default_serializer(obj):
#     if isinstance(obj, datetime):
#         return obj.isoformat()
#     raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")

@tool(args_schema=ScenarioConfig)
def create_scenario(name, centralBody, startTime, endTime, description='') -> dict:
    """
    创建空间场景。
    
    Args:
        name: 场景名称。
        centralBody: 中心天体。
        startTime: 纪元UTC开始时间，例如："2021-05-01T00:00:00.000Z"
        endTime: 纪元UTC结束时间，例如："2021-05-02T00:00:00.000Z"
        description: 场景描述。

    Returns:
        dict: 创建空间场景的指令信息
    """
    log.info(f"创建场景工具: {name}, {centralBody}, {startTime}, {endTime}, {description}")
    args = {
        "name": name,
        "centralBody": centralBody,
        "startTime": startTime,
        "endTime": endTime,
        "description": description
    }
    return Operation(message=f"向平台发送创建场景指令", func="create_scenario", args=args)


@tool
def rename_scenerio(new_name) -> dict:
    """
    修改场景名称。

    Args:
        new_name: 新的场景名称。
    Returns:
        dict: 修改场景名称的指令信息
    """
    log.info(f"重命名场景工具: {new_name}")
    args = {
        "name": new_name
    }
    return Operation(message=f"向平台发送重命名场景指令", func="rename_scenerio", args=args)

@tool(args_schema=EntityConfig)
def add_point_entity(entityType, name, position, properties) -> dict:
    """
    向当前场景添加一个实体(例如：地点、地面站、传感器等)
    但不包括向当前场景添加卫星

    Args:
        entityType: 实体类型。
        name : 实体名称(可选)。
        position: 位置信息 (例如 {"longitude": 116.0, "latitude": 40.0})。
        properties: 其他属性(可选)。

    Returns:
        dict: 添加实体的指令信息。
    """
    args = {
        "entityType": entityType,
        "name": name,
        "position": position,
        "properties": properties
    }
    return Operation(message=f"向平台发送添加实体指令", func="add_point_entity", args=args)

@tool(args_schema=SatelliteTLEParams)
def add_satellite_entity(
    TLEs: Optional[List[str]]=[],
    satellite_number: Optional[str]="",
    start: Optional[str]="",
    end: Optional[str]=""
    ) -> dict:
    """
    向当前场景添加一个实体类型为卫星的对象
    允许全空参数

    Args:
        TLEs: 两行轨道数据
        satellite_number: 卫星编号
        start: 纪元UTC开始时间，例如："2021-05-01T00:00:00.000Z"
        end: 纪元UTC结束时间，例如："2021-05-02T00:00:00.000Z"

    Returns: 添加卫星的指令信息。
    """
        
    log.info(f"add_satellite_entity 已发送卫星计算指令: SatNo={satellite_number}, start={start}, end={end}, TLEs={TLEs}")
    args = {
        "TLEs": TLEs,
        "satellite_number": satellite_number,
        "start": start,
        "end": end
    }
    
    return Operation(message=f"向平台发送添加卫星指令", func="add_satellite_entity", args=args)

@tool
def clear_entities() -> dict:
    """
    清除当前场景中的所有实体。
    
    Returns:
        dict: 清除实体的指令信息。
    """
    log.info("clear_entities 工具 指令发送")
    return Operation(message = "向平台发送清除实体指令", func="clear_entities", args=None)

@tool
def clear_scene() -> dict:
    """
    清除当前场景，包括所有实体和设置。
    
    Returns:
        dict: 清除场景的指令信息。
    """
    log.info("clear_scene 工具 已发送指令")
    return Operation(message = "向平台发送清除场景指令", func="clear_scene", args=None)

write_tools = [create_scenario, rename_scenerio, add_point_entity, add_satellite_entity, clear_entities, clear_scene]