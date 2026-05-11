const { BrowserWindow, ipcMain } = require("electron");
const path = require("path");
const auth = require("../auth");
const api = require("../api");

let loginWindow = null;
let onLoginSuccessCallback = null;

function setOnLoginSuccess(callback) {
  onLoginSuccessCallback = callback;
}

function createLoginWindow() {
  if (loginWindow) {
    loginWindow.focus();
    return loginWindow;
  }

  loginWindow = new BrowserWindow({
    width: 400,
    height: 480,
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
  });

  return loginWindow;
}

function closeLoginWindow() {
  if (loginWindow) {
    loginWindow.close();
    loginWindow = null;
  }
}

async function handleLogin(event, { username, password, serverUrl }) {
  try {
    if (serverUrl && serverUrl !== auth.getServerUrl()) {
      auth.setServerUrl(serverUrl);
    }

    const result = await api.login(username, password);
    closeLoginWindow();
    
    if (onLoginSuccessCallback) {
      onLoginSuccessCallback();
    }
    
    return { success: true, user: result.user };
  } catch (error) {
    const message = error.response?.data?.detail || error.message || "登录失败";
    return { success: false, message };
  }
}

async function handleRegister(event, { username, password, email, serverUrl }) {
  try {
    if (serverUrl && serverUrl !== auth.getServerUrl()) {
      auth.setServerUrl(serverUrl);
    }

    await api.register(username, password, email);
    return { success: true };
  } catch (error) {
    const message = error.response?.data?.detail || error.message || "注册失败";
    return { success: false, message };
  }
}

function handleGetServerUrl() {
  return auth.getServerUrl();
}

function setupIpcHandlers() {
  ipcMain.handle("login:login", handleLogin);
  ipcMain.handle("login:register", handleRegister);
  ipcMain.handle("login:getServerUrl", handleGetServerUrl);
}

module.exports = {
  createLoginWindow,
  closeLoginWindow,
  setupIpcHandlers,
  setOnLoginSuccess,
};
