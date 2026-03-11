import os
from langchain_tavily import TavilySearch
from config import CONFIG

os.environ.setdefault("TAVILY_API_KEY", CONFIG["tavily"]["api_key"])
tavily_tool = TavilySearch(max_results=1)
tavily_tool.description = "这是一个强大的搜索引擎。当用户询问实时信息（如天气、交通、气候）或你无法直接回答的旅行相关问题时，请优先使用此工具进行搜索。"
