"""
工具的作用是发出指令
因为空间态势分析是基于Cesium的前端应用程序，所以工具的作用是发出指令，前端执行相应的操作。
"""
from langchain_core.tools import tool
from agent.space.space_types import ScenarioConfig, EntityConfig, SatelliteTLEParams, ToolResult, EntityType
from infrastructure.logger import log
from typing import Optional, List, Dict, Any

def default_serializer(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")

@tool(args_schema=ScenarioConfig)
def create_scenario(name: str, centralBody: str, startTime: str, endTime: str, description: Optional[str] = None) -> dict:
    """
    创建一个新的空间场景。
    
    Args:
        name (str): 场景名称。
        centralBody (str): 中心天体。
        startTime (str): 纪元UTC开始时间，例如："2021-05-01T00:00:00.000Z"
        endTime (str): 纪元UTC结束时间，例如："2021-05-02T00:00:00.000Z"
        description (Optional[str]): 场景描述。

    Returns:
        ToolResult: 操作结果。
    """
    log.info(f"创建场景工具: {name}, {centralBody}, {startTime}, {endTime}, {description}")

    # 日期格式正则表达式，支持两种格式：
    # 1. YYYY-MM-DD
    # 2. YYYY-MM-DDThh:mm:ss.sssZ (Z可选)
    import re
    date_pattern = r'^\d{4}-\d{2}-\d{2}(?:T\d{2}:\d{2}:\d{2}(?:\.\d{3})?(?:Z)?)?$'
    if not re.match(date_pattern, startTime) or not re.match(date_pattern, endTime):
        return ToolResult(success=False,message="请告诉我创建场景的纪元开始时间和结束时间",func="create_scenario",args=locals()).model_dump()

    try:
        return ToolResult(message=f"场景:{name} 创建成功",func="create_scenario",args=locals()).model_dump()
    except TypeError as e:
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
    return ToolResult(message=f"重命名场景: {new_name}成功", func="rename_scenerio", args=locals())

@tool(args_schema=EntityConfig)
def add_point_entity(name: str, entityType:EntityType,position: Optional[Dict[str, Any]] = None, properties: Optional[Dict[str, Any]] = None) -> dict:
    """
    向当前场景添加一个实体类型为点的对象

    Args:
        name (str): 实体名称。
        entityType (EntityType): 实体类型。
        position (Optional[Dict[str, Any]]): 位置信息 (例如 {"longitude": 116.0, "latitude": 40.0})。
        properties (Optional[Dict[str, Any]]): 其他属性 (例如 TLE)。

    Returns:
        ToolResult: 操作结果。
    """
    return ToolResult(message=f"实体: '{name}', 类型: '{entityType.name}' 已成功添加。", func="add_point_entity", args=locals()).model_dump()

@tool(args_schema=SatelliteTLEParams)
def add_satellite_entity(TLEs: List[str], SatelliteNumber: str, Start: str, Stop: str) -> dict:
    """
    向当前场景添加一个实体类型为卫星的对象
    使用SGP4来计算卫星轨道

    Args:
        TLEs List[str]: 两行轨道数据, 例如：
            ["1 25730U 99025A   21120.62396556  .00000659  00000-0  35583-3 0  9997","2 25730  99.0559 142.6068 0014039 175.9692 333.4962 14.16181681132327"]
        SatelliteNumber (str): 卫星编号，例如："SL-44291"
        Start (str): 纪元UTC开始时间，例如："2021-05-01T00:00:00.000Z"
        Stop (str): 纪元UTC结束时间，例如："2021-05-02T00:00:00.000Z"

    Returns:
        ToolResult: 操作结果。
    """
    log.info(f"add_satellite_entity 已发送卫星计算指令: SatNo={SatelliteNumber}, Start={Start}, Stop={Stop}, TLEs={TLEs}")
    return ToolResult(message=f"卫星 {SatelliteNumber} 的轨道计算完成。", func="add_satellite_entity", args=locals()).model_dump()

@tool
def clear_entities() -> dict:
    """
    清除当前场景中的所有实体。
    
    Returns:
        ToolResult: 操作结果。
    """
    log.info("clear_entities 工具 指令发送")
    return ToolResult(message = "已清除当前场景中的所有实体。", func="clear_entities", args=None).model_dump()

@tool
def clear_scene() -> dict:
    """
    清除当前场景，包括所有实体和设置。
    
    Returns:
        ToolResult: 操作结果。
    """
    log.info("clear_scene 工具 已发送指令")
    return ToolResult(message = "场景已成功清除。", func="clear_scene", args=None).model_dump()

write_tools = [create_scenario, rename_scenerio, add_point_entity, add_satellite_entity, clear_entities, clear_scene]