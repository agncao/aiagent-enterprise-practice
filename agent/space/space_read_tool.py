"""
工具的作用是发出指令
因为空间态势分析是基于Cesium的前端应用程序，所以工具的作用是发出指令，前端执行相应的操作。

这是一个读指令，例如发出查询场景是否存在的指令。
"""
from langchain_core.tools import tool
from agent.space.space_types import ToolResult,CommandType
from infrastructure.logger import log

@tool
def query_scenario(name: str) -> dict:
    '''
    根据场景名称查询场景，其用途：
    1. 当创建场景时需要判断场景是否存在
    2. 查询场景的基本信息

    Args:
        name (str): 场景名称。
    '''
    log.info(f"execute tool: query_scenario, input: {name}")
    result = ToolResult(type=CommandType.READ,message=f"向平台发送查询场景指令",func="query_scene", args=locals()).model_dump()
    return result

@tool
def query_scenario_entities(name: str) -> dict:
    '''
    根据场景名称查询场景所包含的所有实体。
    
    Args:
        name (str): 场景名称。
    '''
    log.info(f"execute tool: query_scenario_entities, input: {name}")
    result = ToolResult(type=CommandType.READ,message=f"向平台发送查询场景实体指令",func="query_scene_entities", args=locals()).model_dump()
    return result

read_tools = [query_scenario, query_scenario_entities]