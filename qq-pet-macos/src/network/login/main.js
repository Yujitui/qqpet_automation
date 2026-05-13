const { BrowserWindow, ipcMain, app } = require("electron");
const path = require("path");
const auth = require("../auth");
const api = require("../api");

let loginWindow = null;
let onLoginSuccessCallback = null;
let isLoginSuccess = false; // 标志位：区分登录成功关闭 vs 用户手动关闭

function setOnLoginSuccess(callback) {
  onLoginSuccessCallback = callback;
}

function createLoginWindow() {
  if (loginWindow) {
    loginWindow.focus();
    return loginWindow;
  }

  isLoginSuccess = false; // 重置标志位，注销后关闭登录窗口应退出程序

  loginWindow = new BrowserWindow({
    width: 325,
    height: 280,
    frame: false,
    transparent: true,
    resizable: false,
    minimizable: false,
    maximizable: false,
    title: "QQ宠物 - 登录",
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, "preload.js"),
    },
  });

  loginWindow.loadFile(path.join(__dirname, "index.html"));

  loginWindow.on("closed", () => {
    loginWindow = null;
    // 如果不是登录成功关闭，且没有其他窗口，立即退出程序
    if (!isLoginSuccess && BrowserWindow.getAllWindows().length === 0) {
      app.exit(0);
    }
    isLoginSuccess = false; // 重置标志位
  });

  return loginWindow;
}

function closeLoginWindow() {
  if (loginWindow) {
    loginWindow.close();
    loginWindow = null;
  }
}

async function handleLogin(event, { username, password }) {
  try {
    const result = await api.login(username, password);

    if (result.status === "created") {
      return { success: true, status: "created", message: result.message || "账号已注册，请联系管理员激活" };
    }

    if (result.status === "active") {
      isLoginSuccess = true; // 标记为登录成功，关闭窗口时不退出
      closeLoginWindow();
      if (onLoginSuccessCallback) {
        onLoginSuccessCallback();
      }
      return { success: true, status: "active" };
    }

    return { success: false, message: "未知错误" };
  } catch (error) {
    if (!error.response) {
      return { success: false, message: "无法连接到服务器，请检查服务器是否已启动" };
    }
    const status = error.response.status;
    if (status === 403) {
      return { success: false, message: "账号未激活，请联系管理员" };
    }
    if (status === 401) {
      return { success: false, message: "密码错误" };
    }
    return { success: false, message: "登录失败，请稍后重试" };
  }
}

function handleCloseWindow() {
  closeLoginWindow();
}

function setupIpcHandlers() {
  ipcMain.handle("login:login", handleLogin);
  ipcMain.handle("login:closeWindow", handleCloseWindow);
}

module.exports = {
  createLoginWindow,
  closeLoginWindow,
  setupIpcHandlers,
  setOnLoginSuccess,
};
