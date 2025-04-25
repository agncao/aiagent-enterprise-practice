import WebSocketClient from "./ws.js";

// agent-comm.js
// 基于ws.js的通用WebSocket双工通讯组件，支持事件驱动和Promise两种调用方式

class AgentComm {
  constructor (wsUrl) {
    this.wsUrl = wsUrl;
    this.wsClient = WebSocketClient.getInstance(wsUrl);
    this.threadId = '';
    this.eventTarget = new EventTarget();
    this.pendingPromises = {};
    this._initEventHandlers();
  }

  _initEventHandlers() {
    this.wsClient.on('open', () => {
      this._emitLog('WebSocket 已连接');
    });
    this.wsClient.on('close', () => {
      this._emitLog('WebSocket 已断开', 'error');
    });
    this.wsClient.on('error', (e) => {
      this._emitLog('WebSocket 错误', 'error');
    });
    this.wsClient.on('message', (data) => {
      let parsed;
      try {
        parsed = JSON.parse(data);
      } catch (e) {
        this._emitLog('收到无法解析的数据: ' + data, 'error');
        return;
      }
      if (parsed.type === 'ai_message') {
        this._emitLog('AI: ' + parsed.content, 'ai');
      } else if (parsed.type === 'tool_call') {
        this._emitLog('[事件驱动] 收到指令: ' + parsed.tool_func, 'tool');
        this.triggerToolEvent(parsed.tool_func, parsed);
        this.sendToolWithPromise(parsed.tool_func, parsed).then(result => {
          this._emitLog('[Promise] 工具执行完成: ' + JSON.stringify(result), 'tool');
        });
        setTimeout(() => {
          const result = { success: true, message: `已模拟执行: ${parsed.tool_func}` };
          this.wsClient.sendMessage({
            type: 'tool_result',
            tool_func: parsed.tool_func,
            result: result,
            thread_id: parsed.thread_id
          });
          this._emitLog('已回传执行结果: ' + JSON.stringify(result), 'tool');
          this.triggerToolEvent(parsed.tool_func + '_result', { result, thread_id: parsed.thread_id });
          this.resolveToolPromise(parsed.tool_func, parsed.thread_id, result);
        }, 1000);
      } else if (parsed.type === 'tool_result') {
        this.triggerToolEvent(parsed.tool_func + '_result', { result: parsed.result, thread_id: parsed.thread_id });
        this.resolveToolPromise(parsed.tool_func, parsed.thread_id, parsed.result);
      } else if (parsed.type === 'end') {
        this._emitLog('本轮对话结束', 'ai');
      } else if (parsed.error) {
        this._emitLog('错误: ' + parsed.error, 'error');
      }
    });
    // 保证连接
    this.wsClient.connect();
  }

  // 日志事件（可选，业务可监听log事件）
  _emitLog(msg, cls = '') {
    this.eventTarget.dispatchEvent(new CustomEvent('log', { detail: { msg, cls } }));
  }

  // 事件驱动注册
  registerToolEvent(toolFunc, callback) {
    this.eventTarget.addEventListener(toolFunc, callback);
  }
  triggerToolEvent(toolFunc, detail) {
    const event = new CustomEvent(toolFunc, { detail });
    this.eventTarget.dispatchEvent(event);
  }

  // Promise异步机制
  sendToolWithPromise(toolFunc, payload) {
    return new Promise((resolve, reject) => {
      const thread_id = payload.thread_id || this.threadId || ('space-thread-' + Date.now());
      const promiseKey = toolFunc + '_' + thread_id;
      this.pendingPromises[promiseKey] = { resolve, reject };
      this.wsClient.sendMessage({ type: 'tool_call', tool_func: toolFunc, ...payload, thread_id });
    });
  }
  resolveToolPromise(toolFunc, thread_id, result) {
    const promiseKey = toolFunc + '_' + thread_id;
    if (this.pendingPromises[promiseKey]) {
      this.pendingPromises[promiseKey].resolve(result);
      delete this.pendingPromises[promiseKey];
    }
  }

  // 发送普通消息
  sendMessage(input, threadId = '') {
    this.threadId = threadId || this.threadId || ('space-thread-' + Date.now());
    if (!input) return;
    this.wsClient.sendMessage({ input, thread_id: this.threadId });
  }
}

// 导出
export default AgentComm;