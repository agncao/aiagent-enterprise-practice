from typing import List, Optional, Dict, Any, TypedDict
from pydantic import BaseModel, Field
from enum import Enum
from typing_extensions import TypedDict, Annotated
from langgraph.graph import add_messages
from datetime import datetime, timedelta, timezone

def get_yesterday_midnight_utc():
    """返回昨天0点的UTC时间，ISO格式"""
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday = today - timedelta(days=1)
    return yesterday.isoformat()

def get_today_midnight_utc():
    """返回今天0点的UTC时间，ISO格式"""
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    return today.isoformat()

class CommandType(Enum):
    """
    指令类型
    """
    READ = "query"
    WRITE = "write"

class ScenarioConfig(BaseModel):
    """
    创建场景所需参数
    """
    name: str = Field("新建场景", description="场景名称")
    centralBody: str = Field("Earth", description="中心天体")
    startTime: str = Field(default_factory=get_yesterday_midnight_utc, description="开始时间(UTC)")
    endTime: str = Field(default_factory=get_today_midnight_utc, description="结束时间(UTC)")
    description: Optional[str] = Field(None, description="场景描述(可选)")

class EntityPosition(BaseModel):
    """
    实体位置的参数信息
    """
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
    """
    创建除卫星之外的实体所需参数
    """
    entityType: EntityType = Field(None, description="实体类型")
    name: Optional[str] = Field(None, description="实体名称")
    position: EntityPosition = Field(None, description="实体位置")
    properties: Optional[Dict[str, Any]] = Field(None, description="实体属性")

class SatelliteTLEParams(BaseModel):
    """
    创建实体为卫星可能需要的参数，之所以是可能，因为所有参数均为可选，允许全空
    """
    # 两行轨道数据，例如：
    # 1 25544U 98067A   23001.75382237  .00000000  00000-0  00000-0  00000-0
    # 2 25544  51.6335  100.0000  0000000  000.0000  000.0000  00000-0 00000
    TLEs: Optional[List[str]] = Field(None, description="两行轨道数据(可选)")
    # 卫星编号，例如："SL-44291"
    satellite_number: Optional[str] = Field(None, description="卫星编号(可选)")
    # 纪元UTC开始时间，例如："2021-05-01T00:00:00.000Z"
    start: Optional[str] = Field(None, description="开始时间(UTC)(可选)")
    # 纪元UTC结束时间，例如："2021-05-02T00:00:00.000Z"
    end: Optional[str] = Field(None, description="结束时间(UTC)(可选)")

class CommandResponse(TypedDict):
    """
    其他应用系统返回的指令执行结果
    """
    success: bool= True # 是否成功
    data: List[Any]= []  # 指令执行返回来的数据
    message: str= ''  # 指令执行返回来的消息
    tool_func: str  # 指令执行的工具名
    args: Dict[str, Any]  # 指令执行的参数
    thread_id: str  # 会话 ID

class Operation(TypedDict, total=False):
    """
    向平台发出的操作指令
    """
    # 指令生成成功与否
    success: bool
    # 指令生成与否的原因
    message: str
    # 指令参数
    args: Optional[Dict[str, Any]]
    # 指令名称
    func: str


class SpaceState(TypedDict):
    """
    Agent 的状态定义
    """
    # 存储对话上下文
    messages: Annotated[list, add_messages]
    # 用户输入
    user_input: str
    # 平台执行工具发出的指令返回结果
    tool_call_response: Optional[Any]
    # 设置完成标志，表示工具执行已完成
    completed: bool = False