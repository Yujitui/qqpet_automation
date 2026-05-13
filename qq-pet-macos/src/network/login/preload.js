const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("loginAPI", {
  login: (data) => ipcRenderer.invoke("login:login", data),
  closeWindow: () => ipcRenderer.invoke("login:closeWindow"),
});
