from langchain_core.runnables import Runnable, RunnableConfig
from langchain_core.tools import tool
from app.multi_agent.state import CtripFlowState
from config import get_logger

logger = get_logger(__name__)


def _classify_error(e: Exception) -> str:
    name = e.__class__.__name__.lower()
    text = str(e).lower()
    if any(k in name or k in text for k in ["timeout", "connection", "dns", "ssl"]):
        return "network"
    if any(k in name or k in text for k in ["unauthorized", "forbidden", "authentication", "api key", "401", "403"]):
        return "auth"
    if any(k in name or k in text for k in ["rate", "429", "quota", "too many requests"]):
        return "rate_limit"
    if any(k in name or k in text for k in ["sqlite", "database", "operationalerror", "locked"]):
        return "database"
    return "code_or_runtime"

class Assistant:
    def __init__(self, runnable: Runnable):
        """
        初始化助手的实例。
        :param runnable: 可以运行对象，通常是一个Runnable类型的
        """
        self.runnable = runnable

    def __call__(self, state: CtripFlowState, config: RunnableConfig):
        """
        调用节点，执行助手任务
        :param state: 当前工作流的状态
        :param config: 配置: 里面有旅客的信息
        :return:
        """
        while True:
            try:
                result = self.runnable.invoke(state, config)
            except Exception as e:
                category = _classify_error(e)
                logger.exception("assistant invoke failed, category=%s", category)
                raise RuntimeError(f"assistant_invoke_failed[{category}]: {e}") from e
            if not result.tool_calls and (
                not result.content
                or isinstance(result.content, list)
                and not result.content[0].get("text")
            ):
                messages = state["messages"] + [("user", "Respond with a real output.")]
                state = {**state, "messages": messages}
            else:
                break
        return {"messages": result}