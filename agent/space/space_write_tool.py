"""
工具的作用是发出指令
因为空间态势分析是基于Cesium的前端应用程序，所以工具的作用是发出指令，前端执行相应的操作。
这是写指令，例如发出添加实体、添加卫星、查询场景等指令。
"""
from typing import List, Optional, Dict, Any, TypedDict
from langchain_core.tools import tool
# 移除 Operation 的导入
from agent.space.space_types import ScenarioConfig, EntityConfig, SGP4Param, EntityType, EntityPosition, ENTITY_TYPE_TEXT,get_utc_strings
from infrastructure.logger import log
from langchain_core.runnables import RunnableConfig
from datetime import datetime


# def default_serializer(obj):
#     if isinstance(obj, datetime):
#         return obj.isoformat()
#     raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")

@tool(args_schema=ScenarioConfig)
def create_scenario(name='新建场景', centralBody='Earth', startTime=None, endTime=None, description="") -> dict:
    """
    创建场景。
    
    Args:
        name: 场景名称。
        centralBody: 中心天体。
        startTime: 纪元UTC开始时间，如果未提供,则为None。
        endTime: 纪元UTC结束时间，如果未提供,则为None。
        description: 场景描述。

    Returns:
        dict: 创建空间场景的指令信息
    """
    log.info(f"创建场景工具: {name}, {centralBody}, {startTime}, {endTime}, {description}")
    
    if not startTime or not endTime:
        yesterday, today = get_utc_strings(datetime.now())
        if not startTime:
            startTime = yesterday
        if not endTime:
            endTime = today
    args = {
        "name": name,
        "centralBody": centralBody,
        "startTime": startTime,
        "endTime": endTime,
        "description": description
    }
    res = {"success":True,"message":f"向平台准备发送创建场景指令", "func":"create_scenario", "args":args}
    return res


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
    # 直接返回字典
    return {"success": True, "message": f"向平台准备发送重命名场景指令", "func": "rename_scenerio", "args": args}

@tool(args_schema=EntityConfig)
def add_point_entity(
    entityType: Optional[str] = None,
    name: Optional[str] = None,
    position: Optional[dict] = None,
    properties: Optional[dict] = None
) -> dict:
    """
    向当前场景添加一个实体(例如：卫星、地面站、传感器等)

    Args:
        entityType (Optional[str]): 实体类型。
        name (Optional[str]): 实体名称。如果未提供，将使用默认值。
        position (Optional[dict]): 实体位置坐标。
        properties (Optional[dict]): 实体的其他属性。
    Returns:
        dict: 添加实体的指令信息。
    """

    final_name = name
    if not final_name and entityType:
        final_name = ENTITY_TYPE_TEXT.get(entityType, "未命名实体")
    elif not final_name:
        final_name = "未命名实体"

    args = {
        "entityType": entityType,
        "name": final_name,
        "position": position,
        "properties": properties or {}
    }
    log.info(f"add_point_entity: 构造的指令参数: {args}")
    # 直接返回字典
    return {"success": True, "message": "向平台准备发送添加实体指令", "func": "add_point_entity", "args": args}

@tool(args_schema=SGP4Param)
def create_SGP4_orbit(
    TLEs: Optional[List[str]]=[],
    satellite_number: Optional[str]="",
    start: Optional[str]="",
    end: Optional[str]=""
    ) -> dict:
    """
    向当前场景添加SGP4模型计算的卫星轨道。
    只有当用户请求中包含有'SGP4'或者'轨道'这两个含义时，才会使用SGP4模型计算卫星轨迹。
    如果单纯的只是添加卫星，不使用SGP4模型计算卫星轨道，那么可以使用add_point_entity工具。
    
    Args:
        TLEs: 两行轨道数据
        satellite_number: 卫星编号
        start: 纪元UTC开始时间，例如："2021-05-01T00:00:00.000Z"
        end: 纪元UTC结束时间，例如："2021-05-02T00:00:00.000Z"

    Returns: SGP4卫星轨道计算指令。
    """
        
    log.info(f"add_satellite_entity 已发送SGP4卫星轨道计算指令: SatNo={satellite_number}, start={start}, end={end}, TLEs={TLEs}")
    args = {
        "TLEs": TLEs,
        "satellite_number": satellite_number,
        "start": start,
        "end": end
    }
    
    # 直接返回字典
    return {"success": True, "message": f"向平台准备发送添加SGP4卫星指令", "func": "create_SGP4_orbit", "args": args}

@tool
def clear_entities() -> dict:
    """
    清除当前场景中的所有实体。
    
    Returns:
        dict: 清除实体的指令信息。
    """
    log.info("clear_entities 工具 指令发送")
    # 直接返回字典
    return {"success": True, "message": "向平台准备发送清除实体指令", "func": "clear_entities", "args": None}

@tool
def clear_scene() -> dict:
    """
    清除当前场景，包括所有实体和设置。
    
    Returns:
        dict: 清除场景的指令信息。
    """
    log.info("clear_scene 工具 已发送指令")
    # 直接返回字典
    return {"success": True, "message": "向平台准备发送清除场景指令", "func": "clear_scene", "args": None}

write_tools = [create_scenario, rename_scenerio, add_point_entity, create_SGP4_orbit, clear_entities, clear_scene]