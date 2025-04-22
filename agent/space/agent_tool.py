from langchain_core.tools import tool
from pydantic import BaseModel

@tool
class UserConfirm(BaseModel):
    """
    是否需要用户确认信息
    """
    request: str