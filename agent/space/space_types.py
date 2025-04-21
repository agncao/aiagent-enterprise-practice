from typing import List, Optional, Dict, Any, TypedDict
from pydantic import BaseModel, Field
from enum import Enum
from langchain_core.messages import BaseMessage
from typing_extensions import TypedDict, Annotated
from langgraph.graph import add_messages


# 对应 ScenarioConfig
class ScenarioConfig(BaseModel):
    name: str = None
    centralBody: str = None
    startTime: str = None
    endTime: str = None
    description: Optional[str] = None

# 对应 EntityConfig
class EntityPosition(BaseModel):
    longitude: float
    latitude: float
    height: Optional[float] = None

class EntityType(Enum):
    GROUND_STATION = "ground_station"
    PLACE = "place"                   # 地点
    TARGET = "target"                 # 目标点
    FACILITY = "facility"             # 地面站
    AIRCRAFT = "aircraft"             # 飞机
    MISSILE = "missile"               # 导弹
    SATELLITE = "satellite"           # 卫星
    SENSOR = "sensor"                 # 传感器
    GROUND_VEHICLE = "groundVehicle"  # 地面车
    SHIP = "ship"                     # 船
    LAUNCH_VEHICLE = "launchVehicle"  # 火箭
    LINE_TARGET = "lineTarget"        # 线目标
    AREA_TARGET = "areaTarget"        # 区域目标
    CHAIN = "chain"                   # 链路

class EntityConfig(BaseModel):
    entityType: Optional[EntityType] = None
    name: Optional[str] = None
    position: Optional[EntityPosition] = None
    properties: Optional[Dict[str, Any]] = None

# 对应 SatelliteTLEParams
class SatelliteTLEParams(BaseModel):
    # 纪元UTC开始时间，例如："2021-05-01T00:00:00.000Z"
    Start: str
    # 纪元UTC结束时间，例如："2021-05-02T00:00:00.000Z"
    Stop: str
    # 卫星编号，例如："SL-44291"
    SatelliteNumber: str
    # 两行轨道数据
    TLEs: List[str]
    
class ConversationState(Enum):
    IDLE = 'idle'                     # 空闲状态
    COLLECTING_INFO = 'collecting_info' # 收集信息状态
    CONFIRMING = 'confirming'         # 确认信息状态
    EXECUTING = 'executing'           # 执行操作状态
    ERROR = 'error'                   # 错误状态

# 对应 ToolResult
class ToolResult(BaseModel):
    success: bool
    message: str
    args: Optional[Any] = None
    func: str

# Agent 的状态定义，结合了 ConversationContext 和 BaseState 的概念
class SpaceState(TypedDict):
     # 存储对话上下文
    messages: Annotated[list, add_messages]
    # 用户输入
    user_input: str
    # 动作类型，例如 "tool_call"
    action: str = None 
    # 工具调用的名称 例如: tool_call的['function']['name']
    tool_func:str = None 
    # 工具调用所需参数 例如：tool_call['function']['arguments']
    tool_func_args: dict = None
    # 工具调用返回结果 status 0 代表失败，1 代表成功
    act_result: dict = {"status":"0","data":[],"message":"success"}
    # 设置完成标志，表示工具执行已完成
    completed: bool = False
