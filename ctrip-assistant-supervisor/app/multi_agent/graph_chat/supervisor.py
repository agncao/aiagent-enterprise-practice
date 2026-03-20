from langchain.agents import create_agent

from app.multi_agent.llm import llm
from app.multi_agent.graph_chat.task_handoff import build_handoff_tools


def build_supervisor():
    return create_agent(
        tools=build_handoff_tools(),
        model=llm,
        system_prompt=(
            "你是一个监督者或者管理者，管理五个智能体：\n"
            "- 网络搜索智能体：分配与网络搜索、数据查询相关的任务\n"
            "- 航班预订能体：分配与航班查询，预定，改签等相关的任务\n"
            "- 酒店预订智能体：分配与酒店查询，预定，修改订单等相关的任务\n"
            "- 汽车租赁预定智能体：分配与汽车租赁查询，预定，修改订单等相关的任务\n"
            "- 旅行产品预定智能体：分配与旅行推荐查询，预定，修改订单等相关的任务\n"
            "处理规则：\n"
            "1. 如果问题属于以下类别，直接回答：\n"
            "   - 可以根据上下文记录直接回答的内容（如'你的航班信息，起飞时间等'）。\n"
            "   - 不需要工具的一般咨询（如'你好'）。\n"
            "   - 确认类问题（如'你收到我的请求了吗'）。\n"
            "2. 其他情况按类型分配给对应智能体。\n"
            "3. 一次只分配一个任务给一个智能体。\n"
            "4. 不要自己执行需要工具的任务。\n"
        ),
        name="supervisor"
    )

