from abc import ABC
from app.agent.state import State, BaseState

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from utils.langgraph_utils import *
import time
from langchain_core.runnables import Runnable, RunnablePassthrough, RunnableLambda
from infrastructure.logger import log


class BaseAssistant(ABC):
    def __init__(self, llm):
        self.llm = llm
        self.tools = []
        self.worker = None
        self.state = BaseState(
            messages=[],
            params={},
            user_input="",
            result=None,
            params_ready=False,
            assistant_name=self.__class__.__name__,
            assistant_type=None
        )
    
    def get_system_prompt(self) -> str:
        pass
    
    def check_params(self, state: BaseState) -> dict:
        pass

    def agent_node(self, state: BaseState) -> BaseState:
        """
        执行助理节点的逻辑
        - 执行航班信息查询入参校验工具
        - 如果入参校验通过，则执行search_flights工具查询航班信息
        - 如果入参校验不通过，则向用户请求缺失的信息
        Args:
            state (BaseState): 当前状态
        Returns:
            BaseState: 更新后的状态
        """
        log.debug("agent_node start: last message is:", state["messages"][-1] if len(state["messages"]) > 0 else "")

        if not (len(state["messages"]) > 0 and isinstance(state["messages"][-1], HumanMessage)):
            state["messages"].append(HumanMessage(content=state["user_input"]))
        
        agent = self._create_agent_executor()
        
        try:
            result = agent.invoke({"user_input": state["user_input"]})
            log.debug("agent_node Agent执行结果:", result)
            
            # 检查是否有工具调用
            if hasattr(result, "tool_calls") and result.tool_calls:
                # 如果有工具调用，添加一个系统消息告知用户
                tool_names = []
                for tool_call in result.tool_calls:
                    if hasattr(tool_call, "function") and hasattr(tool_call.function, "name"):
                        tool_name = tool_call.function.name
                        tool_names.append(tool_name)
                        log.debug("Agent执行工具: ", tool_name)
                
                # 根据工具名称生成合适的消息
                if "check_params" in tool_names:
                    message = "我正在处理您的请求，请稍候..."
                elif "search_flights" in tool_names:
                    message = "正在为您搜索航班信息，请稍候..."
                else:
                    message = f"正在使用工具 {', '.join(tool_names)} 处理您的请求，请稍候..."
                
                # 添加 AI 消息
                ai_message = AIMessage(content=message)
                state["messages"].append(ai_message)
                print("\nAssistant:", message)
            else:
                # 添加 AI 消息到状态
                ai_message = AIMessage(content=result.content)
                state["messages"].append(ai_message)
                # 直接打印 AI 消息
                print("\nAssistant:", ai_message.content)
        except Exception as e:
            log.error("Agent执行出错", str(e))
            raise e
        return state

    def _create_agent_executor(self) -> Runnable:
        """
        创建助理的代理执行器
        Returns:
            代理执行器
        """
        llm_with_tools = self.llm.bind_tools(tools=self.tools)
        prompt = ChatPromptTemplate.from_messages([
            ("system", self.get_system_prompt()),
            MessagesPlaceholder(variable_name="history_messages"),
            ("user", "{user_input}"),
        ])

        input_dict = RunnablePassthrough.assign(
            history_messages=lambda x: self.state["messages"]
        )
        return input_dict | prompt | llm_with_tools

    def build(self):
        pass
    
    def initial_state(self) -> BaseState:
        """
        初始化状态
        
        Returns:
            BaseState: 初始状态
        """
        return BaseState(
            messages=[],
            params={},
            user_input="",
            result=None,
            params_ready=False,
            assistant_name=self.__class__.__name__,
            assistant_type=self.state["assistant_type"]
        )

    # 运行工作流
    def run_assistant(self):
        """
        运行助理工作流，处理用户输入并生成响应
        使用 utils/langgraph_utils.py 中的方法简化流程
        """
        self.worker = self.worker or self.build()
        print("如果需要退出，请输入'退出','quit','q','exit' 任意一项。")
        
        # 创建会话ID
        session_id = str(int(time.time()))
        config = {
            "configurable": {
                "thread_id": session_id
            }
        }
        
        while True:
            try:
                user_input = input('用户: ')
                if user_input.lower() in ['q', 'exit', 'quit', '退出']:
                    print('对话结束，拜拜！')
                    break
                else:
                    # 执行工作流
                    loop_graph_invoke(self.worker, user_input, config)
                    
                    # 查看此时的状态
                    state_snapshot = self.worker.get_state(config)
                    
                    # 检查是否有工具调用需要人工干预
                    if hasattr(state_snapshot, 'next') and 'tools' in state_snapshot.next:
                        # 可以人工介入
                        tools_script_message = state_snapshot.values['messages'][-1]
                        log.debug('Tools Script: ', tools_script_message.tool_calls)

                        if input('人工客户输入是否继续工具调用: yes或者no').lower() == 'yes':
                            # 继续执行下一个节点: tools
                            loop_graph_invoke_tools(self.worker, None, config)
                        else:
                            # 用户输入了no， 那就需要自己添加一个Message
                            get_answer(tools_script_message)
                    
                    # 检查是否已完成查询
                    state_dict = dict(state_snapshot.values) if hasattr(state_snapshot, 'values') else {}
                    if "params_ready" in state_dict and state_dict["params_ready"] and "result" in state_dict and state_dict["result"]:
                        print("\n查询结果为:", state_dict["result"])
                        break

            except Exception as e:
                log.error("发生错误", str(e))
                raise e