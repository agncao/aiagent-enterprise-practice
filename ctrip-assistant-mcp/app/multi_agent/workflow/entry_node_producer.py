from langchain_core.messages import ToolMessage
from typing import Callable
from app.multi_agent.state import CtripFlowState
from config import get_logger

logger = get_logger(__name__)

def create_entry_node(assistant_name: str, new_dialog_state: str) -> Callable:
    """
    这是一个函数工程： 创建一个入口节点函数，当对话状态转换时调用。
    该函数生成一条新的对话消息，并更新对话的状态。

    :param assistant_name: 新助理的名字或描述。
    :param new_dialog_state: 要更新到的新对话状态。
    :return: 返回一个根据给定的assistant_name和new_dialog_state处理对话状态的函数。
    """
    
    def entry_node(state: CtripFlowState) -> CtripFlowState:
        """
        处理对话状态转换，生成新的对话消息并更新状态。

        :param state: 当前的对话状态。
        :return: 更新后的对话状态。
        """
        # 生成新的对话消息
        new_message = (
            f"现在助手是{assistant_name}。请回顾上述主助理与用户之间的对话。"
            f"用户的意图尚未满足。使用提供的工具协助用户。记住，您是{assistant_name}，"
            "并且预订、更新或其他操作未完成，直到成功调用了适当的工具。"
            "如果用户改变主意或需要帮助进行其他任务，请调用CompleteOrEscalate函数让主要的主助理接管。"
            "不要提及你是谁——仅作为助理的代理。"
        )
        
        logger.info(f"进入到{assistant_name}, 入口节点:{new_dialog_state}")
        # 更新对话状态
        return {
            "dialog_state": new_dialog_state,
            "messages": [ToolMessage(content=new_message, tool_call_id=state["messages"][-1].tool_calls[0]["id"])],
        }
    
    return entry_node  