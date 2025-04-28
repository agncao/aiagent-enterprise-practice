"""
工具的作用是发出指令
因为空间态势分析是基于Cesium的前端应用程序，所以工具的作用是发出指令，前端执行相应的操作。

这是一个读指令，例如发出查询场景是否存在的指令。
"""
from langchain_core.tools import tool
from agent.space.space_types import CommandInfo,CommandType
from infrastructure.logger import log

@tool
def query_scenario(name: str) -> CommandInfo:
    '''
    根据场景名称查询场景

    Args:
        name (str): 场景名称。
    Returns:
        CommandInfo: 查询场景的指令信息
    '''
    log.info(f"execute tool: query_scenario, input: {name}")
    result = CommandInfo(type=CommandType.READ,message=f"向平台发送查询场景指令",func="query_scene", args=locals()).model_dump()
    return result

@tool
def query_scenario_entities() -> CommandInfo:
    '''
    查询当前场景所包含的所有实体。
    
    Returns:
        CommandInfo: 查询场景实体的指令信息
    '''
    log.info(f"execute tool: query_scenario_entities")
    result = CommandInfo(type=CommandType.READ,message=f"向平台发送查询场景实体指令",func="query_scene_entities").model_dump()
    return result

read_tools = [query_scenario, query_scenario_entities]