"""
工具的作用是发出指令
因为空间态势分析是基于Cesium的前端应用程序，所以工具的作用是发出指令，前端执行相应的操作。
"""
from langchain_core.tools import tool
from agent.space.space_types import ScenarioConfig, EntityConfig, SatelliteTLEParams, ToolResult, EntityType, EntityPosition
from infrastructure.logger import log
from typing import Optional, List, Dict, Any

@tool(args_schema=ScenarioConfig)
def create_scenario(name: str, centralBody: str, startTime: str, endTime: str, description: Optional[str] = None) -> ToolResult:
    """
    创建一个新的空间场景。
    
    Args:
        name (str): 场景名称。
        centralBody (str): 中心天体。
        startTime (str): 开始时间。
        endTime (str): 结束时间。
        description (Optional[str]): 场景描述。

    Returns:
        ToolResult: 操作结果。
    """
    log.info(f"模拟创建场景: {name}, {centralBody}, {startTime}, {endTime}, {description}")
    # 在实际应用中，这里会调用 YYASTK 或其他服务的 API
    # result_from_backend = call_yyastk_create_scenario(...)
    success = True 
    message = f"场景 '{name}' 已成功创建。" if success else "场景创建失败。"
    return ToolResult(success=success, message=message, func="createScene", args=locals())

@tool
def rename_scenerio(new_name: str) -> ToolResult:
    """
    重命名当前场景。

    Args:
        new_name (str): 新的场景名称。
    Returns:
        ToolResult: 操作结果。
    """
    log.info(f"模拟重命名场景: {new_name}")
    # 在实际应用中，这里会调用 YYASTK 或其他服务的 API
    # result_from_backend = call_yyastk_rename_scenerio(...)
    success = True
    message = f"场景已成功重命名为 '{new_name}'。" if success else "场景重命名失败。"
    return ToolResult(success=success, message=message, func="renameScene", args=locals())

@tool(args_schema=EntityConfig)
def add_point_entity(name: str, entityType:EntityType,position: Optional[Dict[str, Any]] = None, properties: Optional[Dict[str, Any]] = None) -> ToolResult:
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
    log.info(f"模拟添加实体: {EntityType.PLACE}, {name}, position={position}, properties={properties}")
    # 在实际应用中，这里会调用 YYASTK 或其他服务的 API
    # result_from_backend = call_yyastk_add_entity(...)
    success = True 
    message = f"实体: '{name}', 类型: '{EntityType.PLACE}' 已成功添加。" if success else "实体添加失败。"
    return ToolResult(success=success, message=message, func="addPointEntity", args=locals())

@tool(args_schema=SatelliteTLEParams)
def add_satellite_entity(
    Start: str,
    Stop: str,
    SatelliteNumber: str,
    TLEs: List[str]
) -> ToolResult:
    """
    向当前场景添加一个实体类型为卫星的对象
    使用SGP4来计算卫星轨道

    Args:
        Start: 纪元UTC开始时间，例如："2021-05-01T00:00:00.000Z"
        Stop: 纪元UTC结束时间，例如："2021-05-02T00:00:00.000Z"
        SatelliteNumber: 卫星编号，例如："SL-44291"
        TLEs: 两行轨道数据
    Returns:
        ToolResult: 操作结果。
    """
    log.info(f"卫星轨道计算: SatNo={SatelliteNumber}, Start={Start}, Stop={Stop}, TLEs={TLEs}")
    # 在实际应用中，这里会调用轨道计算库或服务
    success = True
    message = f"卫星 {SatelliteNumber} 的轨道计算完成。" if success else "轨道计算失败。"
    # 实际应用中可能返回计算出的位置数据
    return ToolResult(success=success, message=message, func="addSatelliteEntity", args=locals())
@tool
def clear_entities() -> ToolResult:
    """
    清除当前场景中的所有实体。
    
    Returns:
        ToolResult: 操作结果。
    """
    log.info("模拟清除所有实体")
    success = True 
    message = "所有实体已成功清除。" if success else "清除实体失败。"
    return ToolResult(success=success, message=message, func="clearEntities", args=None)

@tool
def clear_scene() -> ToolResult:
    """
    清除当前场景，包括所有实体和设置。
    
    Returns:
        ToolResult: 操作结果。
    """
    log.info("模拟清除场景")
    success = True 
    message = "场景已成功清除。" if success else "清除场景失败。"
    return ToolResult(success=success, message=message, func="clearScene", args=None)

@tool
def confirm_user_action(action_description: str, details: Dict[str, Any]) -> Dict[str, Any]:
    """
    在执行创建或修改操作前，调用此工具向用户确认信息。

    Args:
        action_description (str): 需要确认的操作描述 (例如 "创建以下场景", "添加以下实体")。
        details (Dict[str, Any]): 需要用户确认的具体信息。

    Returns:
        Dict[str, Any]: 一个包含确认请求的消息，引导用户确认。
    """
    log.info(f"请求用户确认操作: {action_description}, 细节: {details}")
    details_str = "\n".join([f"- {k}: {v}" for k, v in details.items() if v is not None])
    prompt = f"请确认是否要{action_description}：\n{details_str}\n请输入 '是' 或 '否'。"
    # 同样，这个工具生成一个需要AI回复给用户的提示
    return {"prompt_to_user": prompt}

# 将所有工具收集到一个列表中
space_tools = [confirm_user_action,create_scenario, rename_scenerio, add_point_entity, add_satellite_entity, clear_entities, clear_scene]