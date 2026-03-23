from mcp.server.fastmcp import FastMCP
from typing import Optional, Union, List, Dict
from datetime import datetime, date
import json

# 导入所有原有的LangChain工具
from app.multi_agent.tools.flight_tools import (
    search_flights,
    fetch_user_flight_information,
)
from app.multi_agent.tools.hotel_tools import (
    search_hotels
)
from app.multi_agent.tools.car_rental_tools import (
    search_car_rentals
)
from app.multi_agent.tools.trip_recommendation_tools import (
    search_trip_recommendations,
)

# 创建 FastMCP 实例
mcp = FastMCP("ctrip-assistant-mcp-server")

# ====================
# 航班工具
# ====================
@mcp.tool()
def mcp_search_flights(
    departure_airport: Optional[str] = None,
    arrival_airport: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    limit: int = 20
) -> str:
    """搜索航班"""
    # 处理日期格式转换
    st = datetime.fromisoformat(start_time) if start_time else None
    et = datetime.fromisoformat(end_time) if end_time else None
    
    result = search_flights.invoke({
        "departure_airport": departure_airport,
        "arrival_airport": arrival_airport,
        "start_time": st,
        "end_time": et,
        "limit": limit
    })
    return json.dumps(result, ensure_ascii=False)

@mcp.tool()
def mcp_fetch_user_flight_information(passenger_id: str) -> str:
    """获取指定乘客的航班和机票信息"""
    result = fetch_user_flight_information.invoke({}, config={"configurable": {"passenger_id": passenger_id}})
    return json.dumps(result, ensure_ascii=False)


# ====================
# 酒店工具
# ====================
@mcp.tool()
def mcp_search_hotels(location: Optional[str] = None, name: Optional[str] = None) -> str:
    """搜索酒店"""
    result = search_hotels.invoke({"location": location, "name": name})
    return json.dumps(result, ensure_ascii=False)

# ====================
# 租车工具
# ====================
@mcp.tool()
def mcp_search_car_rentals(location: Optional[str] = None, name: Optional[str] = None) -> str:
    """搜索租车服务"""
    result = search_car_rentals.invoke({"location": location, "name": name})
    return json.dumps(result, ensure_ascii=False)


# ====================
# 旅行推荐工具
# ====================
@mcp.tool()
def mcp_search_trip_recommendations(location: Optional[str] = None, name: Optional[str] = None, keywords: Optional[str] = None) -> str:
    """搜索旅行推荐"""
    result = search_trip_recommendations.invoke({"location": location, "name": name, "keywords": keywords})
    return json.dumps(result, ensure_ascii=False)


if __name__ == "__main__":
    # 使用 stdio 模式启动 mcp server
    mcp.run(transport="stdio", port=8256)
