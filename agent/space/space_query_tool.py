from langchain_core.tools import tool
from agent.space.space_types import ToolResult,CommandType
from infrastructure.logger import log

@tool
def query_scenario_exists(name: str) -> dict:
    log.info(f"查询场景是否存在: {name}")
    result = ToolResult(type=CommandType,func="query_scenario_exists", args=locals())
    return result

@tool
def query_scenario_entities(name: str) -> dict:
    log.info(f"查询场景实体: {name}")
    result = ToolResult(type=CommandType.QUERY,func="query_scenario_entities", args=locals())
    return result

query_tools = [query_scenario_exists, query_scenario_entities]