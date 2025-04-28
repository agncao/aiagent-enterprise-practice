from typing import List, Optional, Dict, Any, TypedDict
from pydantic import BaseModel, Field
from enum import Enum
from typing_extensions import TypedDict, Annotated
from langgraph.graph import add_messages
from datetime import datetime

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
    name: str = Field(None, description="场景名称")
    centralBody: str = Field("Earth", description="中心天体")
    startTime: datetime = Field(None, description="开始时间(UTC)")
    endTime: datetime = Field(None, description="结束时间(UTC)")
    description: Optional[str] = Field(None, description="场景描述")

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
    创建实体为卫星所需的参数
    """
    # 纪元UTC开始时间，例如："2021-05-01T00:00:00.000Z"
    start: Optional[datetime] = Field(None, description="开始时间(UTC)")
    # 纪元UTC结束时间，例如："2021-05-02T00:00:00.000Z"
    end: Optional[datetime] = Field(None, description="结束时间(UTC)")
    # 卫星编号，例如："SL-44291"
    satellite_number: Optional[str] = Field(None, description="卫星编号")
    # 两行轨道数据
    TLEs: List[str] = Field(None, description="必须是严格遵守TLE格式的两行轨道数据")

class CommandResponse(TypedDict):
    """
    其他应用系统返回的指令执行结果
    """
    success: bool= True # 是否成功
    data: List[Any]= []  # 指令执行返回来的数据
    message: str= ''  # 指令执行返回来的消息
    tool_func: str  # 指令执行的工具名
    args: Dict[str, Any]  # 指令执行的参数
    tool_call_id: str  # 指令执行的工具调用 ID
    thread_id: str  # 会话 ID

class ToolInfo(BaseModel):
    """
    从 SpaceState 中获取工具调用的 name, args, type, call_id 等信息
    """
    name: str = Field('', description="工具名称")
    args: dict = Field(None, description="工具参数")
    type: str = Field('', description="工具类型")
    call_id: str = Field('', description="工具调用 ID")

class CommandInfo(BaseModel):
    """
    智能体调用工具后，工具向其他应用系统发出的指令信息
    """
    success: bool = Field(True, description="指令是否创建成功")
    data: list[Any] = []
    message: str = Field('', description="指令创建成功或者失败的消息")
    args: Optional[Dict[str, Any]] = Field(None, description="给其他应用系统的发送指令的参数")
    func: str = Field('', description="给其他应用系统的发送指令的名称")
    type: Optional[CommandType] = Field(CommandType.WRITE, description="命令类型")
class SpaceState(TypedDict):
    """
    Agent 的状态定义
    """
    # 存储对话上下文
    messages: Annotated[list, add_messages]
    # 用户输入
    user_input: str
    # 外部系统工具调用信息
    tool_info: Optional[ToolInfo]
    # 工具调用返回结果
    tool_result: Optional[CommandInfo]
    # 设置完成标志，表示工具执行已完成
    completed: bool = False
    # 用户是否已确认了参数信息
    has_answered: bool = False

    def __str__(self):
        return str(self.__dict__)
