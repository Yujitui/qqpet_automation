const { app } = require("electron");
const Store = require("electron-store");

const store = new Store({
  name: "auth-config",
  fileExtension: "json",
  clearInvalidConfig: true,
});

let serverUrl = store.get("serverUrl") || "http://localhost:8000";

function getAccessToken() {
  return store.get("accessToken") || null;
}

function getRefreshToken() {
  return store.get("refreshToken") || null;
}

function getUser() {
  return store.get("user") || null;
}

function setTokens(accessToken, refreshToken, user = null) {
  store.set("accessToken", accessToken);
  store.set("refreshToken", refreshToken);
  if (user) {
    store.set("user", user);
  }
}

function clearTokens() {
  store.delete("accessToken");
  store.delete("refreshToken");
  store.delete("user");
}

function isAuthenticated() {
  return !!getAccessToken();
}

function getServerUrl() {
  return serverUrl;
}

function setServerUrl(url) {
  serverUrl = url;
  store.set("serverUrl", url);
}

module.exports = {
  getAccessToken,
  getRefreshToken,
  getUser,
  setTokens,
  clearTokens,
  isAuthenticated,
  getServerUrl,
  setServerUrl,
};
