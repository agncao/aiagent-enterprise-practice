class WebSocketClient {
    static instances = {};

    static getInstance(url) {
        if (!WebSocketClient.instances[url]) {
            WebSocketClient.instances[url] = new WebSocketClient(url);
        }
        return WebSocketClient.instances[url];
    }

    constructor(url) {
        if (WebSocketClient.instances[url]) {
            return WebSocketClient.instances[url];
        }
        this._ws = null;
        this.url = url;
        this._reconnectCount = 0;
        this._maxReconnectCount = 3;
        this._messageHandlers = [];
        this._eventHandlers = { open: [], close: [], error: [], message: [] };
        WebSocketClient.instances[url] = this;
    }

    // 建立WebSocket连接
    connect() {
        try {
            this._ws = new WebSocket(this.url);
            this._initEventHandlers();
        } catch (error) {
            console.error('WebSocket连接失败:', error);
            this._reconnect();
        }
    }

    // 初始化WebSocket事件处理（私有方法）
    _initEventHandlers() {
        this._ws.onopen = () => {
            console.log('WebSocket连接已建立');
            this._reconnectCount = 0;
            this._emitEvent('open');
        };

        this._ws.onclose = () => {
            console.log('WebSocket连接已关闭');
            this._emitEvent('close');
            this._reconnect();
        };

        this._ws.onerror = (error) => {
            console.error('WebSocket错误:', error);
            this._emitEvent('error', error);
        };

        this._ws.onmessage = (event) => {
            const data = event.data;
            // 触发所有消息处理回调
            this._messageHandlers.forEach(handler => handler(data));
            this._emitEvent('message', data);
        };
    }

    // 重连机制（私有方法）
    _reconnect() {
        if (this._reconnectCount < this._maxReconnectCount) {
            this._reconnectCount++;
            console.log(`尝试第${this._reconnectCount}次重连...`);
            setTimeout(() => {
                this.connect();
            }, 3000);
        }
    }

    // 发送消息
    sendMessage(message) {
        if (this._ws && this._ws.readyState === WebSocket.OPEN) {
            this._ws.send(typeof message === 'string' ? message : JSON.stringify(message));
        } else {
            console.error('WebSocket未连接，无法发送消息');
        }
    }

    // 添加消息监听器
    onMessage(callback) {
        if (typeof callback === 'function') {
            this._messageHandlers.push(callback);
        }
    }

    // 移除消息监听器
    removeMessageHandler(callback) {
        const index = this._messageHandlers.indexOf(callback);
        if (index !== -1) {
            this._messageHandlers.splice(index, 1);
        }
    }

    // 添加事件监听器
    on(event, callback) {
        if (this._eventHandlers[event] && typeof callback === 'function') {
            this._eventHandlers[event].push(callback);
        }
    }

    // 移除事件监听器
    off(event, callback) {
        if (this._eventHandlers[event]) {
            const idx = this._eventHandlers[event].indexOf(callback);
            if (idx !== -1) {
                this._eventHandlers[event].splice(idx, 1);
            }
        }
    }

    // 触发事件（私有方法）
    _emitEvent(event, ...args) {
        if (this._eventHandlers[event]) {
            this._eventHandlers[event].forEach(cb => {
                try {
                    cb(...args);
                } catch (e) {
                    console.error('事件回调异常:', e);
                }
            });
        }
    }

    // 支持Promise发送消息
    sendMessageWithPromise(message) {
        return new Promise((resolve, reject) => {
            if (this._ws && this._ws.readyState === WebSocket.OPEN) {
                this._ws.send(typeof message === 'string' ? message : JSON.stringify(message));
                const handler = (data) => {
                    resolve(data);
                    this.off('message', handler);
                };
                this.on('message', handler);
            } else {
                reject('WebSocket未连接，无法发送消息');
            }
        });
    }

    // 关闭连接
    close() {
        if (this._ws) {
            this._ws.close();
        }
    }
}

export default WebSocketClient;
