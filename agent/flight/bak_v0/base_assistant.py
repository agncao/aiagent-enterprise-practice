from abc import ABC
from agent.state import State
from app.utils.langgraph_utils import *

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.runnables import Runnable, RunnablePassthrough
import time
from infrastructure.logger import log


class BaseAssistant(ABC):
    def __init__(self, llm):
        """
        初始化助理
        
        Args:
            llm: 语言模型
        """
        self.llm = llm
        self.tools = []
        self.state = {"messages": []}
        self.worker = None

    def get_system_prompt(self):
        pass

    def check_params(self, state: State):
        pass

    def agent_node(self, state: State):
        """
        代理节点，处理用户输入，调用LLM生成回复
        
        Args:
            state (State): 当前状态
        
        Returns:
            dict: 包含messages和next字段的字典
        """
        log.debug("进入agent_node，当前状态: {}", state)
        
        # 初始化反馈信息
        feedback = {"messages": [], "params_ready": False}
        
        # 如果最后一条消息不是用户消息，则添加用户输入
        if not (len(state["messages"]) > 0 and isinstance(state["messages"][-1], HumanMessage)):
            feedback["messages"].append(HumanMessage(content=state["user_input"]))
        
        agent = self._create_agent_executor()
        
        try:
            response = agent.invoke({"user_input": state["user_input"]})
            log.debug("agent_node Agent执行结果: {}", response)
            
            # 添加回复到消息列表
            if "output" in response:
                feedback["messages"].append(AIMessage(content=response["output"]))
            
            # 检查是否需要执行工具
            feedback["next"] = "tools"
            
        except Exception as e:
            log.error("代理执行器执行出错: {}", str(e))
            # 添加错误消息
            feedback["messages"].append(AIMessage(content="抱歉，我遇到了一些问题，请稍后再试。"))
            feedback["next"] = "end"
        
        log.debug("agent_node执行完毕，反馈信息: {}", feedback)
        return feedback

    def _create_agent_executor(self):
        """
        创建代理执行器
        
        Returns:
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
