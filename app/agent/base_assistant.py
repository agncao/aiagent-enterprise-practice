from abc import ABC
from app.agent.state import State
from app.utils.langgraph_utils import *

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.runnables import Runnable, RunnablePassthrough
import time
from infrastructure.logger import log


class BaseAssistant(ABC):
    def __init__(self, llm):
        self.llm = llm
        self.tools = []
        self.worker = None
        self.state = State(messages=[])

    def get_system_prompt(self):
        pass

    def check_params(self, state: State):
        pass

    def agent_node(self, state: State):
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
        feedback = {"messages": [],"params_ready": False}
        if not (len(state["messages"]) > 0 and isinstance(state["messages"][-1], HumanMessage)):
            feedback["messages"].append(HumanMessage(content=state["user_input"]))
        
        agent = self._create_agent_executor()
        
        try:
            response = agent.invoke({"user_input": state["user_input"]})
            log.debug("agent_node Agent执行结果: {}", response)
            
            # 检查是否有工具调用
            if hasattr(response, "tool_calls") and response.tool_calls:
                log.debug("agent 工具调用: {}", response.tool_calls)

                # 如果有工具调用，添加一个系统消息告知用户
                tool_calls = [e for e in response.tool_calls]
                # List comprehension for newer ChatOpenAI versions
                tool_names = [
                    tool_call['name'] if isinstance(tool_call, dict) and 'name' in tool_call
                    else tool_call.name if hasattr(tool_call, 'name')
                    else None
                    for tool_call in response.tool_calls
                ]
                
                if tool_names and "search_flights" in tool_names:
                    feedback["params_ready"] = True
                
                # 添加工具调用消息
                feedback["messages"].append(AIMessage(content=response.content, tool_calls=response.tool_calls))
            else:
                # 如果没有工具调用，只添加普通消息
                feedback["messages"].append(AIMessage(content=response.content))
        except Exception as e:
            log.error("Agent执行出错: {}", str(e))
            raise e
        return feedback

    def _create_agent_executor(self) -> Runnable:
        """
        创建助理的代理执行器
        Returns:
            代理执行器
        """
        # 确保工具列表不为空
        if not self.tools:
            log.warning("工具列表为空，可能导致工具调用失败")
        
        # 绑定工具到 LLM
        log.debug("绑定工具到 LLM: {}", [getattr(tool, "name", str(tool)) for tool in self.tools])
        llm_with_tools = self.llm.bind_tools(tools=self.tools, tool_choice="auto")
        
        # 创建提示模板
        prompt = ChatPromptTemplate.from_messages([
            ("system", self.get_system_prompt()),
            MessagesPlaceholder(variable_name="history_messages"),
            ("user", "{user_input}"),
        ])
        
        # 创建输入字典
        input_dict = RunnablePassthrough.assign(
            history_messages=lambda x: self.state["messages"]
        )
        
        # 返回代理执行器
        return input_dict | prompt | llm_with_tools

    def build(self):
        pass


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
                if user_input.lower() in ['q', 'exit', 'quit']:
                    print('对话结束，拜拜！')
                    break
                else:
                    self.state["user_input"] = user_input
                    
                    # 执行 工作流
                    loop_graph_invoke(self.worker, user_input, config)
                    # 查看此时的状态
                    now_state = self.worker.get_state(config)
                    log.debug("当前状态: {}", now_state)

                    # 检查下一个节点是否为tools
                    if hasattr(now_state, 'next') and 'tools' in now_state.next:
                        # 可以人工介入
                        tools_script_message = now_state.values['messages'][-1]  # 状态中存储的最后一个message
                        log.debug('Tools Script: {}', tools_script_message.tool_calls)
                        
                        loop_graph_invoke_tools(self.worker, None, config)
                    else:
                        # 说明没有工具调用，直接结束
                        break
            except Exception as e:
                log.error("发生错误: {}", str(e))
                raise e
