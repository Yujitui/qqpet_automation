// macOS: 全局 EPIPE 防护 — 必须在最前面
// 原项目有几百个 console.log，管道断开时会 EPIPE 崩溃
const _origLog = console.log;
const _origErr = console.error;
const _origWarn = console.warn;
const safeFn = (fn) => (...args) => { try { fn(...args); } catch (e) { if (e?.code !== "EPIPE") throw e; } };
console.log = safeFn(_origLog);
console.error = safeFn(_origErr);
console.warn = safeFn(_origWarn);
process.stdout?.on?.("error", () => {});
process.stderr?.on?.("error", () => {});
process.on("uncaughtException", (err) => {
  if (err.code === "EPIPE" || err.message?.includes("EPIPE")) return;
});

const { app } = require("electron");
const path = require("path");

const gotTheLock = app.requestSingleInstanceLock();

// 禁用测试后门
global.$test = false;

global.initData = {};

let useTool = null;
let tool = ["floatStyle"];

try {
  let e = process.argv;
  for (let t in tool) {
    let a = false;
    for (let o in e) {
      if (e[o].indexOf(tool[t]) !== -1) {
        initData.NODE_TOOL = tool[t];
        a = true;
        break;
      }
    }
    if (a) break;
  }
} catch (e) {}

if (process?.env?.NODE_TOOL) {
  initData.NODE_TOOL = process.env.NODE_TOOL;
}

if (initData?.NODE_TOOL && typeof initData?.NODE_TOOL === "string") {
  useTool = require("./src/windows/tool/" + initData.NODE_TOOL + "/main.js");
}

// 网络层
const auth = require("./src/network/auth");
const loginManager = require("./src/network/login/main");
const remoteStore = require("./src/ini/remoteStore");

// 阻止自动退出：所有窗口关闭后继续运行（托盘图标应用需要）
app.on("window-all-closed", () => {
  console.log("All windows closed, keeping app running (tray mode)");
});

async function startMainGame() {
  console.log("[startMainGame] Starting...");

  if (!gotTheLock) {
    console.log("[startMainGame] Another instance running, exiting");
    app.exit(true);
    return;
  }

  try {
    console.log("[startMainGame] Setting up environment...");
    process.env.ELECTRON_DISABLE_SECURITY_WARNINGS = "true";
    app.setAppUserModelId("pet");

    if (useTool) {
      console.log("[startMainGame] Tool mode:", initData.NODE_TOOL);
      useTool.cleate("only");
      console.log("[startMainGame] Tool started");
      return;
    }

    // 初始化 RemoteStore
    console.log("[startMainGame] Initializing RemoteStore...");
    await remoteStore.init();
    console.log("[startMainGame] RemoteStore ready, isRemoteMode:", remoteStore.isRemoteMode);

    // 加载 init.js
    console.log("[startMainGame] Loading init.js...");
    require("./src/ini/init.js");
    console.log("[startMainGame] init.js loaded");

    // 关键：init.js 中的 store.js 会设置 global.$Store
    // 所以必须在 init.js 加载后重新设置为 RemoteStore
    global.$Store = remoteStore;
    console.log("[startMainGame] global.$Store set to RemoteStore (after init.js)");

    // 加载 doMain.js
    console.log("[startMainGame] Loading doMain.js...");
    require("./src/ini/doMain.js");
    console.log("[startMainGame] doMain.js loaded");

    console.log("[startMainGame] Main game fully started!");

  } catch (err) {
    console.error("[startMainGame] ERROR:", err.message);
    console.error("[startMainGame] Stack:", err.stack);
    // 即使出错也不退出，保持应用运行
  }
}

const createWindow = async () => {
  loginManager.setupIpcHandlers();

  loginManager.setOnLoginSuccess(() => {
    console.log("Login success, starting main game...");
    startMainGame();
  });

  global.onAuthRequired = () => {
    console.log("Auth required, showing login window");
    loginManager.createLoginWindow();
  };

  global.onKicked = (reason) => {
    console.log("Kicked from server:", reason);
    loginManager.createLoginWindow();
  };

  if (useTool) {
    startMainGame();
    return;
  }

  // 保持原始的 unhandledRejection 行为（完全静默）
  process.on("unhandledRejection", function (e, t) {});

  if (auth.isAuthenticated()) {
    try {
      const api = require("./src/network/api");
      await api.getCurrentUser();
      console.log("Token valid, starting game...");
      startMainGame();
      return;
    } catch (e) {
      console.log("Token invalid, clearing tokens:", e.message);
      auth.clearTokens();
    }
  }

  console.log("Showing login window...");
  loginManager.createLoginWindow();
};

// macOS: 不加载 PepFlash DLL（使用 Ruffle WASM 替代）
app.commandLine.appendSwitch("disable-site-isolation-trials");

app.whenReady().then(() => {
  createWindow();
});
