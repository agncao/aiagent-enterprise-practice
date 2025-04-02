from enum import Enum, auto

class AssistantType(Enum):
    """
    助理类型枚举，定义系统支持的各种助理类型
    """
    HOTEL = auto()
    FLIGHT = auto()
    CAR = auto()
    
    def __str__(self):
        return self.name.lower()
    
    @classmethod
    def from_string(cls, name: str):
        """从字符串创建枚举值，不区分大小写"""
        try:
            return cls[name.upper()]
        except KeyError:
            raise ValueError(f"Unknown assistant type: {name}")
