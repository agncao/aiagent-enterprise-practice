from typing import Union
from pydantic import BaseModel, Field


class GraphConfigurableSchema(BaseModel):
    """调用工作流的configurable 的Schema"""
    passenger_id: str = Field(description='旅客的ID号', default="3442 587242")
    thread_id: str = Field(description='会话ID', default=None)

class GraphConfigSchema(BaseModel):
    """配置的Schema"""
    configurable: Union[GraphConfigurableSchema, None] = Field(description='封装配置', default=None)

class BaseGraphSchema(BaseModel):
    """基础的工作流调用Schema"""
    config: Union[GraphConfigSchema, None] = Field(description='配置', default=None)
    user_input: str = Field(description='用户输入', default=None)

class GraphResponseSchema(BaseModel):
    """工作流执行完成之后的输出 类型"""
    assistant: str = Field(description='工作流执行后，AI助手响应内容', default=None)