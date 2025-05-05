from typing import List, Optional, Dict, Any, TypedDict
from pydantic import BaseModel, Field,validator
from enum import Enum
from typing_extensions import TypedDict, Annotated
from langgraph.graph import add_messages
from datetime import datetime, timedelta, timezone 

def get_utc_strings(dt: datetime):
    """
    将dt及dt的前一天生成UTC 时间的 ISO 8601 格式字符串 (带 Z)，例如: "2023-10-26T00:00:00.000Z"
    :return: (pre_day_str, current_day_str)：入参的前一天和入参当天的UTC时间，格式：YYYY-MM-DDTHH:mm:ss.sssZ
    """
    pre_day_datetime = dt - timedelta(days=1)
    format = "%Y-%m-%dT00:00:00.000Z"

    # 格式化为 ISO 8601 字符串 (带 Z)
    pre_day_str = pre_day_datetime.strftime(format)
    current_day_str = dt.strftime(format)

    return pre_day_str, current_day_str


class ScenarioConfig(BaseModel):
    """
    创建场景所需参数
    """
    name: Optional[str] = Field("新建场景", description="场景名称")
    centralBody: Optional[str] = Field("Earth", description="中心天体")
    startTime: Optional[str] = Field(None, description="开始时间(UTC),格式：YYYY-MM-DDTHH:mm:ss.sssZ")
    endTime: Optional[str] = Field(None, description="结束时间(UTC),格式：YYYY-MM-DDTHH:mm:ss.sssZ")
    description: Optional[str] = Field(None, description="场景描述(可选)")

class EntityPosition(TypedDict): 
    """
    实体位置的参数信息
    """
    longitude: Optional[float] = Field(None, description="经度")
    latitude: Optional[float] = Field(None, description="纬度")
    height: Optional[float] = Field(None, description="高度，单位：米")

class EntityType(Enum):
    """
    实体类型
    表示在空物体的类型，例如：地面站、卫星、飞机、传感器、地面车等
    """
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

# 新增：定义 EntityType 到中文名称的映射
ENTITY_TYPE_TEXT = {
    EntityType.PLACE.value: "地点",
    EntityType.TARGET.value: "目标点",
    EntityType.FACILITY.value: "地面站",
    EntityType.AIRCRAFT.value: "飞机",
    EntityType.MISSILE.value: "导弹",
    EntityType.SATELLITE.value: "卫星",
    EntityType.SENSOR: "传感器",
    EntityType.GROUND_VEHICLE.value: "地面车",
    EntityType.SHIP.value: "船",
    EntityType.LAUNCH_VEHICLE.value: "火箭",
    EntityType.LINE_TARGET.value: "线目标",
    EntityType.AREA_TARGET.value: "区域目标",
    EntityType.CHAIN.value: "链路",
}


class EntityConfig(BaseModel):
    """
    创建实体所需参数
    """
    entityType: Optional[EntityType] = Field(None, description="实体类型") 
    name: Optional[str] = Field(None, description="实体名称")
    position: Optional[EntityPosition] = Field(None, description="实体位置")
    properties: Optional[Dict[str, Any]] = Field(None, description="实体属性")

    @validator("entityType", pre=True)
    def convert_entity_type(cls, v):
        """将字符串自动转换为枚举实例"""
        if isinstance(v, str):
            try:
                return EntityType(v.lower())
            except ValueError:
                pass  # 保持原始值触发后续验证
        return v

    class Config:
        use_enum_values = True
        json_encoders = {
            EntityType: lambda e: e.value  # 确保枚举序列化为字符串
        }

class SGP4Param(BaseModel):
    """
    创建创建SGP4卫星轨道参数，允许全空
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

# 删除以下 Operation 类定义 (原 L130-141)
# class Operation(TypedDict, total=False):
#     """
#     向平台发出的操作指令
#     """
#     # 指令生成成功与否
#     success: bool
#     # 指令生成与否的原因
#     message: str
#     # 指令参数
#     args: Optional[Dict[str, Any]]
#     # 指令名称
#     func: str


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