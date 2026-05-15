const crypto = require("crypto");
const WebSocket = require("ws");
const auth = require("./auth");
const { getWsUrl } = require("./api");

class WSClient {
  constructor() {
    this.ws = null;
    this.isConnected = false;
    this._listeners = {};
    this._pendingRequests = {};
    this._reconnectAttempts = 0;
    this._maxReconnectDelay = 30000;
    this._reconnectTimer = null;
    this._shouldReconnect = true;
    this._pendingMessages = [];
    this._onOpenCallback = null;
    this._onCloseCallback = null;
    this._onErrorCallback = null;
  }

  set onOpen(cb) { this._onOpenCallback = cb; }
  set onClose(cb) { this._onCloseCallback = cb; }
  set onError(cb) { this._onErrorCallback = cb; }

  async connect() {
    const token = auth.getAccessToken();
    if (!token) {
      console.log("[WSClient] No token available, skipping connect");
      return;
    }

    const url = getWsUrl() + "?token=" + encodeURIComponent(token);
    this._shouldReconnect = true;

    try {
      this.ws = new WebSocket(url);
    } catch (e) {
      console.log("[WSClient] Failed to create WebSocket:", e.message);
      this._scheduleReconnect();
      return;
    }

    this.ws.onopen = () => {
      console.log("[WSClient] Connected");
      this.isConnected = true;
      this._reconnectAttempts = 0;

      for (const msg of this._pendingMessages) {
        this._sendRaw(msg);
      }
      this._pendingMessages = [];

      if (this._onOpenCallback) this._onOpenCallback();
    };

    this.ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        this._dispatch(msg);
      } catch (e) {
        console.log("[WSClient] Failed to parse message:", e.message);
      }
    };

    this.ws.onclose = (event) => {
      console.log("[WSClient] Disconnected, code:", event.code);
      this.isConnected = false;
      this.ws = null;

      this._rejectAllPending({ error: "connection closed", code: event.code });

      if (event.code === 1008) {
        console.log("[WSClient] Policy violation (1008), token may be invalid");
        if (global.onAuthRequired) {
          global.onAuthRequired();
        }
        this._shouldReconnect = false;
      }

      if (this._onCloseCallback) this._onCloseCallback(event.code);
      if (this._shouldReconnect) this._scheduleReconnect();
    };

    this.ws.onerror = (err) => {
      console.log("[WSClient] Error");
      if (this._onErrorCallback) this._onErrorCallback(err);
    };
  }

  disconnect() {
    this._shouldReconnect = false;
    if (this._reconnectTimer) {
      clearTimeout(this._reconnectTimer);
      this._reconnectTimer = null;
    }
    if (this.ws) {
      try { this.ws.close(); } catch (e) {}
      this.ws = null;
    }
    this.isConnected = false;
  }

  send(router, action, data = {}) {
    const msg = {
      router,
      action,
      data,
      id: crypto.randomUUID(),
      timestamp: Date.now(),
    };
    if (this.isConnected && this.ws) {
      this._sendRaw(msg);
    } else {
      this._pendingMessages.push(msg);
    }
    return msg.id;
  }

  async request(router, action, data = {}, timeout = 5000) {
    const id = this.send(router, action, data);
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        delete this._pendingRequests[id];
        reject(new Error("request timeout"));
      }, timeout);

      this._pendingRequests[id] = { resolve, reject, timer };
    });
  }

  on(router, callback) {
    if (!this._listeners[router]) {
      this._listeners[router] = [];
    }
    this._listeners[router].push(callback);
  }

  off(router, callback) {
    if (!this._listeners[router]) return;
    this._listeners[router] = this._listeners[router].filter(
      (cb) => cb !== callback
    );
    if (this._listeners[router].length === 0) {
      delete this._listeners[router];
    }
  }

  _sendRaw(msg) {
    try {
      this.ws.send(JSON.stringify(msg));
    } catch (e) {
      console.log("[WSClient] Send failed:", e.message);
    }
  }

  _dispatch(msg) {
    const msgId = msg.id;
    if (msgId && this._pendingRequests[msgId]) {
      const { resolve, timer } = this._pendingRequests[msgId];
      clearTimeout(timer);
      delete this._pendingRequests[msgId];
      resolve(msg);
      return;
    }

    const router = msg.router || "";
    for (const [prefix, callbacks] of Object.entries(this._listeners)) {
      if (router.startsWith(prefix)) {
        for (const cb of callbacks) {
          try { cb(msg); } catch (e) {
            console.log("[WSClient] Listener error:", e.message);
          }
        }
      }
    }
  }

  _scheduleReconnect() {
    const delay = Math.min(
      1000 * Math.pow(2, this._reconnectAttempts),
      this._maxReconnectDelay
    );
    this._reconnectAttempts++;
    console.log(`[WSClient] Reconnecting in ${delay}ms (attempt ${this._reconnectAttempts})`);
    this._reconnectTimer = setTimeout(() => this.connect(), delay);
  }

  _rejectAllPending(reason) {
    for (const [id, { reject, timer }] of Object.entries(this._pendingRequests)) {
      clearTimeout(timer);
      reject(reason);
    }
    this._pendingRequests = {};
  }
}

const wsClient = new WSClient();
module.exports = wsClient;
