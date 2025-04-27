"""
工具的作用是发出指令
因为空间态势分析是基于Cesium的前端应用程序，所以工具的作用是发出指令，前端执行相应的操作。
"""
from langchain_core.tools import tool
from agent.space.space_types import ScenarioConfig, EntityConfig, SatelliteTLEParams, ToolResult, EntityType, EntityPosition
from infrastructure.logger import log
from typing import Optional, List, Dict, Any
from datetime import datetime

# def default_serializer(obj):
#     if isinstance(obj, datetime):
#         return obj.isoformat()
#     raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")

@tool(args_schema=ScenarioConfig)
def create_scenario(name: str, centralBody: str, startTime: datetime, endTime: datetime, description: Optional[str] = None) -> dict:
    """
    创建一个新的空间场景。
    
    Args:
        name (str): 场景名称。
        centralBody (str): 中心天体。
        startTime (datetime): 纪元UTC开始时间，例如："2021-05-01T00:00:00.000Z"
        endTime (datetime): 纪元UTC结束时间，例如："2021-05-02T00:00:00.000Z"
        description (Optional[str]): 场景描述。

    Returns:
        ToolResult: 操作结果。
    """
    log.info(f"创建场景工具: {name}, {centralBody}, {startTime}, {endTime}, {description}")
    try:
        # Pydantic's model_dump handles datetime serialization correctly by default (to ISO format string)
        return ToolResult(message=f"向平台发送创建场景指令",func="create_scenario",args=locals()).model_dump()
    except TypeError as e:
        # This specific TypeError should now be less likely
        log.error(f"Error serializing args: {e}")
        return ToolResult(success=False,message=f"发生了系统异常",func="create_scenario",args=locals()).model_dump()

@tool
def rename_scenerio(new_name: str) -> ToolResult:
    """
    重命名当前场景。

    Args:
        new_name (str): 新的场景名称。
    Returns:
        ToolResult: 操作结果。
    """
    log.info(f"重命名场景工具: {new_name}")
    return ToolResult(message=f"向平台发送重命名场景指令", func="rename_scenerio", args=locals())

@tool(args_schema=EntityConfig)
def add_point_entity(name: Optional[str] = None, 
                     entityType:EntityType = None,
                     position: EntityPosition = None, 
                     properties: Optional[Dict[str, Any]] = None) -> dict:
    """
    向当前场景添加一个实体类型为点的对象

    Args:
        name (Optional[str]): 实体名称(可选)。
        entityType (EntityType): 实体类型。
        position (EntityPosition): 位置信息 (例如 {"longitude": 116.0, "latitude": 40.0})。
        properties (Optional[Dict[str, Any]]): 其他属性(可选)。

    Returns:
        ToolResult: 操作结果。
    """
    return ToolResult(message=f"向平台发送添加实体指令", func="add_point_entity", args=locals()).model_dump()

@tool(args_schema=SatelliteTLEParams)
def add_satellite_entity(TLEs: List[str], SatelliteNumber: Optional[str] = None, start: Optional[datetime] = None, end: Optional[datetime] = None) -> dict:
    """
    向当前场景添加一个实体类型为卫星的对象
    使用SGP4来计算卫星轨道

    特别注意：入参TLEs必须严格遵守TLE格式

    Args:
        TLEs List[str]: 严格遵守TLE格式的两行轨道数据。
        SatelliteNumber (str): 卫星编号，例如："SL-44291"(可选)。
        start (datetime): 纪元UTC开始时间，例如："2021-05-01T00:00:00.000Z"(可选)。
        end (datetime): 纪元UTC结束时间，例如："2021-05-02T00:00:00.000Z"(可选)。

    Returns:
        ToolResult: 操作结果。
    """
    log.info(f"add_satellite_entity 已发送卫星计算指令: SatNo={SatelliteNumber}, start={start}, end={end}, TLEs={TLEs}")
    return ToolResult(message=f"向平台发送添加卫星指令", func="add_satellite_entity", args=locals()).model_dump()

@tool
def clear_entities() -> dict:
    """
    清除当前场景中的所有实体。
    
    Returns:
        ToolResult: 操作结果。
    """
    log.info("clear_entities 工具 指令发送")
    return ToolResult(message = "向平台发送清除实体指令", func="clear_entities", args=None).model_dump()

@tool
def clear_scene() -> dict:
    """
    清除当前场景，包括所有实体和设置。
    
    Returns:
        ToolResult: 操作结果。
    """
    log.info("clear_scene 工具 已发送指令")
    return ToolResult(message = "向平台发送清除场景指令", func="clear_scene", args=None).model_dump()

write_tools = [create_scenario, rename_scenerio, add_point_entity, add_satellite_entity, clear_entities, clear_scene]