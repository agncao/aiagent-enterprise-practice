from langchain_core.tools import tool
from agent.space.space_types import ScenarioConfig, EntityConfig, SatelliteTLEParams, ToolResult, EntityType
from infrastructure.logger import log
from typing import Optional, List, Dict, Any

@tool(args_schema=ScenarioConfig)
def create_scenario(name: str, centralBody: str, startTime: str, endTime: str, description: Optional[str] = None) -> dict:
    log.info(f"模拟创建场景: {name}, {centralBody}, {startTime}, {endTime}, {description}")
    success = True 
    message = f"场景 '{name}' 已成功创建。" if success else "场景创建失败。"
    return ToolResult(success=success, message=message, func="createScene", args=locals()).model_dump()

@tool
def rename_scenerio(new_name: str) -> ToolResult:
    log.info(f"模拟重命名场景: {new_name}")
    success = True
    message = f"场景已成功重命名为 '{new_name}'。" if success else "场景重命名失败。"
    return ToolResult(success=success, message=message, func="renameScene", args=locals())

@tool(args_schema=EntityConfig)
def add_point_entity(name: str, entityType:EntityType,position: Optional[Dict[str, Any]] = None, properties: Optional[Dict[str, Any]] = None) -> dict:
    log.info(f"模拟添加实体: {EntityType.PLACE}, {name}, position={position}, properties={properties}")
    success = True 
    message = f"实体: '{name}', 类型: '{EntityType.PLACE}' 已成功添加。" if success else "实体添加失败。"
    return ToolResult(success=success, message=message, func="addPointEntity", args=locals()).model_dump()

@tool(args_schema=SatelliteTLEParams)
def add_satellite_entity(Start: str, Stop: str, SatelliteNumber: str, TLEs: List[str]) -> dict:
    log.info(f"卫星轨道计算: SatNo={SatelliteNumber}, Start={Start}, Stop={Stop}, TLEs={TLEs}")
    success = True
    message = f"卫星 {SatelliteNumber} 的轨道计算完成。" if success else "轨道计算失败。"
    return ToolResult(success=success, message=message, func="addSatelliteEntity", args=locals())

@tool
def clear_entities() -> dict:
    log.info("模拟清除所有实体")
    success = True 
    message = "所有实体已成功清除。" if success else "清除实体失败。"
    return ToolResult(success=success, message=message, func="clearEntities", args=None).model_dump()

@tool
def clear_scene() -> dict:
    log.info("模拟清除场景")
    success = True 
    message = "场景已成功清除。" if success else "清除场景失败。"
    return ToolResult(success=success, message=message, func="clearScene", args=None).model_dump()

write_tools = [create_scenario, rename_scenerio, add_point_entity, add_satellite_entity, clear_entities, clear_scene]