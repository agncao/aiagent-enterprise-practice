from typing import List, Optional, Dict, Any, TypedDict
from pydantic import BaseModel, Field
from enum import Enum
from langchain_core.messages import BaseMessage
from typing_extensions import TypedDict, Annotated
from langgraph.graph import add_messages
from datetime import datetime

class CommandType(Enum):
    READ = "query"
    WRITE = "write"

# 对应 ScenarioConfig
class ScenarioConfig(BaseModel):
    name: str = Field(None, description="场景名称")
    centralBody: str = Field("Earth", description="中心天体")
    startTime: datetime = Field(None, description="开始时间(UTC)")
    endTime: datetime = Field(None, description="结束时间(UTC)")
    description: Optional[str] = Field(None, description="场景描述")

# 对应 EntityConfig
class EntityPosition(BaseModel):
    longitude: float = Field(None, description="经度")
    latitude: float = Field(None, description="纬度")
    height: Optional[float] = Field(None, description="高度")

class EntityType(Enum):
    """
    实体类型
    表示在空物体的类型，例如：地面站、卫星、飞机、传感器、地面车等
    """
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
    entityType: EntityType = Field(None, description="实体类型")
    name: Optional[str] = Field(None, description="实体名称")
    position: EntityPosition = Field(None, description="实体位置")
    properties: Optional[Dict[str, Any]] = Field(None, description="实体属性")

# 对应 SatelliteTLEParams
class SatelliteTLEParams(BaseModel):
    # 纪元UTC开始时间，例如："2021-05-01T00:00:00.000Z"
    start: Optional[datetime] = Field(None, description="开始时间(UTC)")
    # 纪元UTC结束时间，例如："2021-05-02T00:00:00.000Z"
    end: Optional[datetime] = Field(None, description="结束时间(UTC)")
    # 卫星编号，例如："SL-44291"
    satellite_number: Optional[str] = Field(None, description="卫星编号")
    # 两行轨道数据
    TLEs: List[str] = Field(None, description="轨道数据")


# 对应 ToolResult
class ToolResult(BaseModel):
    success: bool = Field(True, description="是否成功")
    message: str = Field('', description="消息")
    args: Optional[Any] = None
    func: str = Field('', description="函数名")
    type: Optional[CommandType] = Field(CommandType.WRITE, description="命令类型")
    data: list[Any] = []

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
    # 工具调用返回结果
    tool_result: Optional[ToolResult]    
    # 设置完成标志，表示工具执行已完成
    completed: bool = False

    def __str__(self):
        return str(self.__dict__)
