const { BrowserWindow, ipcMain } = require("electron");
const path = require("path");
const api = require("../../../network/api");

let friendsWindow = null;

function createFriendsWindow() {
  if (friendsWindow) {
    friendsWindow.focus();
    return friendsWindow;
  }

  friendsWindow = new BrowserWindow({
    width: 280,
    height: 440,
    frame: false,
    resizable: false,
    minimizable: false,
    maximizable: false,
    alwaysOnTop: true,
    title: "我的好友",
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, "preload.js"),
    },
  });

  friendsWindow.loadFile(path.join(__dirname, "index.html"));

  friendsWindow.on("closed", () => {
    friendsWindow = null;
  });

  return friendsWindow;
}

function closeFriendsWindow() {
  if (friendsWindow) {
    friendsWindow.close();
    friendsWindow = null;
  }
}

async function handleGetFriends() {
  try {
    return await api.getFriends();
  } catch (e) {
    return [];
  }
}

async function handleGetPending() {
  try {
    return await api.getPendingFriendRequests();
  } catch (e) {
    return [];
  }
}

async function handleAddFriend(event, { nickname }) {
  try {
    const result = await api.addFriend(nickname);
    return { success: true, data: result };
  } catch (e) {
    const msg = e.response?.data?.detail || "添加失败";
    return { success: false, message: msg };
  }
}

async function handleRespond(event, { friendId, action }) {
  try {
    const result = await api.respondFriendRequest(friendId, action);
    return { success: true, data: result };
  } catch (e) {
    return { success: false, message: e.response?.data?.detail || "操作失败" };
  }
}

async function handleRemove(event, { friendId }) {
  try {
    await api.removeFriend(friendId);
    return { success: true };
  } catch (e) {
    return { success: false, message: e.response?.data?.detail || "删除失败" };
  }
}

async function handleUpdateNickname(event, { nickname }) {
  try {
    const result = await api.updateNickname(nickname);
    return { success: true, data: result };
  } catch (e) {
    const status = e.response?.status;
    if (status === 409) return { success: false, message: "该昵称已被使用" };
    return { success: false, message: e.response?.data?.detail || "修改失败" };
  }
}

async function handleGetMe() {
  try {
    const user = await api.getCurrentUser();
    return { success: true, data: user };
  } catch (e) {
    return { success: false, message: "获取用户信息失败" };
  }
}

function setupIpcHandlers() {
  ipcMain.handle("friends:getList", handleGetFriends);
  ipcMain.handle("friends:getPending", handleGetPending);
  ipcMain.handle("friends:add", handleAddFriend);
  ipcMain.handle("friends:respond", handleRespond);
  ipcMain.handle("friends:remove", handleRemove);
  ipcMain.handle("friends:updateNickname", handleUpdateNickname);
  ipcMain.handle("friends:getMe", handleGetMe);
  ipcMain.handle("friends:closeWindow", closeFriendsWindow);
}

module.exports = {
  createFriendsWindow,
  closeFriendsWindow,
  setupIpcHandlers,
};
