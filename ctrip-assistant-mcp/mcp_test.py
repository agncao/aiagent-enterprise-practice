import asyncio
from mcp.client.session import ClientSession
from mcp.client.sse import sse_client

async def run_test():
    # 连接到你启动的 SSE 服务地址
    url = "http://127.0.0.1:8000/mcp/sse"
    print(f"正在连接 MCP 服务: {url}")
    
    # 建立 SSE 客户端连接
    async with sse_client(url) as streams:
        # 建立会话
        async with ClientSession(streams[0], streams[1]) as session:
            await session.initialize()
            
            # 1. 列出所有可用的工具
            print("\n--- 可用工具列表 ---")
            tools = await session.list_tools()
            for tool in tools.tools:
                print(f"- {tool.name}: {tool.description}")
            
            # 2. 尝试调用某个工具（例如查酒店）
            print("\n--- 测试调用 mcp_search_hotels ---")
            try:
                # 传入与工具定义的 JSON Schema 相匹配的参数
                result = await session.call_tool(
                    "mcp_search_hotels", 
                    arguments={"location": "北京"}
                )
                print("调用结果:", result)
            except Exception as e:
                print(f"调用失败: {e}")

if __name__ == "__main__":
    asyncio.run(run_test())