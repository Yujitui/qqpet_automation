const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("loginAPI", {
  login: (data) => ipcRenderer.invoke("login:login", data),
  register: (data) => ipcRenderer.invoke("login:register", data),
  getServerUrl: () => ipcRenderer.invoke("login:getServerUrl"),
});
