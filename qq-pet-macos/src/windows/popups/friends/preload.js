const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("friendsAPI", {
  getList: () => ipcRenderer.invoke("friends:getList"),
  getPending: () => ipcRenderer.invoke("friends:getPending"),
  addFriend: (data) => ipcRenderer.invoke("friends:add", data),
  respondRequest: (data) => ipcRenderer.invoke("friends:respond", data),
  removeFriend: (data) => ipcRenderer.invoke("friends:remove", data),
  updateNickname: (data) => ipcRenderer.invoke("friends:updateNickname", data),
  getMe: () => ipcRenderer.invoke("friends:getMe"),
  closeWindow: () => ipcRenderer.invoke("friends:closeWindow"),
});
