"""
工具的作用是发出指令
因为空间态势分析是基于Cesium的前端应用程序，所以工具的作用是发出指令，前端执行相应的操作。

这是一个读指令，例如发出查询场景是否存在的指令。
"""
from langchain_core.tools import tool
from infrastructure.logger import log


@tool
def query_scenario_entities() -> dict:
    '''
    查询当前场景所包含的所有实体。
    
    Returns:
        dict: 查询场景实体的指令信息
    '''
    log.info(f"execute tool: query_scenario_entities")
    # 直接返回字典
    result = {"success": True, "message": f"向平台准备发送查询场景实体指令", "func": "query_scenario_entities", "args": None}
    return result

read_tools = [query_scenario_entities]