// 引入通用WebSocket双工通讯组件
import AgentComm from "./agent-comm.js";

// DOM 元素获取
const logDiv = document.getElementById("log");
const userInput = document.getElementById("userInput");
const threadIdInput = document.getElementById("threadId");
const sendBtn = document.getElementById("sendBtn");

// 初始化 AgentComm 实例
const agentComm = new AgentComm("ws://localhost:8028/ws/space");

// 日志输出
function appendLog(msg, cls = "") {
  const div = document.createElement("div");
  if (cls) div.className = cls;
  div.innerText = msg;
  logDiv.appendChild(div);
  logDiv.scrollTop = logDiv.scrollHeight;
}

// 统一日志事件监听
agentComm.eventTarget.addEventListener("log", (e) => {
  const { msg, cls } = e.detail;
  appendLog(msg, cls);
});

// 事件注册函数
function registerAgentEvents() {
  // AI 消息
  agentComm.eventTarget.addEventListener("ai_message", (e) => {
    const { content } = e.detail || {};
    appendLog("AI: " + content, "ai");
  });
  // 工具调用
  agentComm.eventTarget.addEventListener("tool_call", (e) => {
    const { tool_func, thread_id } = e.detail;
    agentComm._emitLog(
      `[事件驱动] 收到智能体指令: ${tool_func} (thread_id: ${thread_id})`,
      "tool"
    );
    // 可根据 tool_func 类型弹窗、表单或自动处理
    // 示例：直接模拟回传结果
    setTimeout(() => {
      const result = { success: true, message: `已模拟执行: ${tool_func}` };
      agentComm.wsClient.sendMessage({
        type: "tool_result",
        tool_func,
        result,
        thread_id,
      });
      agentComm._emitLog("已回传执行结果: " + JSON.stringify(result), "tool");
      agentComm.triggerToolEvent(tool_func + "_result", { result, thread_id });
      agentComm.resolveToolPromise(tool_func, thread_id, result);
    }, 1000);
  });
  // 工具结果
  agentComm.eventTarget.addEventListener("tool_result", (e) => {
    const { result } = e.detail || {};
    agentComm._emitLog(
      "[事件驱动] 工具执行结果: " + JSON.stringify(result),
      "tool"
    );
  });
  // 对话结束
  agentComm.eventTarget.addEventListener("end", () => {
    agentComm._emitLog("本轮对话结束", "ai");
  });
}

// 注册事件
registerAgentEvents();

// 示例：注册自定义工具事件监听
agentComm.registerToolEvent("demo_tool", (e) => {
  agentComm._emitLog(
    "[事件驱动] demo_tool 被触发，参数: " + JSON.stringify(e.detail),
    "tool"
  );
});
agentComm.registerToolEvent("demo_tool_result", (e) => {
  agentComm._emitLog(
    "[事件驱动] demo_tool 执行结果: " + JSON.stringify(e.detail),
    "tool"
  );
});

// 用户输入处理
function handleSend() {
  const input = userInput.value.trim();
  const threadId = threadIdInput.value.trim();
  if (!input) return;
  agentComm.sendMessage({
    type: "user_input",
    content: input,
    thread_id: threadId,
    message_id: Digitals.uniqueId(),
  });
  appendLog("你: " + input);
  userInput.value = "";
}
sendBtn.onclick = handleSend;
userInput.addEventListener("keydown", function (e) {
  if (e.key === "Enter") handleSend();
});

// Promise 方式调用工具示例
// 你可以根据实际业务注册更多事件和调用 Promise 接口
agentComm
  .sendToolWithPromise("demo_tool", { thread_id: "test", param1: "示例参数" })
  .then((res) => {
    agentComm._emitLog(
      "[Promise] demo_tool 执行结果: " + JSON.stringify(res),
      "tool"
    );
  });
