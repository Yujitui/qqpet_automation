let currentTab = "friends";
let friendsData = [];
let pendingData = [];
let myNickname = "";
let isEditingNickname = false;
let refreshTimer = null;
const REFRESH_MS = 10000;

// --- Window ---
function closeWindow() {
  window.friendsAPI.closeWindow();
}

// --- Toast ---
function showToast(msg, type) {
  const t = document.getElementById("toast");
  t.textContent = msg;
  t.className = "toast " + type + " show";
  setTimeout(() => t.classList.remove("show"), 2000);
}

// --- Tabs ---
function switchTab(tab) {
  currentTab = tab;
  document.querySelectorAll(".tab-item").forEach(el => el.classList.remove("active"));
  document.querySelector('.tab-item[data-tab="' + tab + '"]').classList.add("active");
  render();
}

// --- Nickname ---
function toggleNicknameEdit() {
  const display = document.getElementById("nicknameDisplay");
  const input = document.getElementById("nicknameInput");
  const btn = document.getElementById("nicknameBtn");

  if (!isEditingNickname) {
    display.style.display = "none";
    input.style.display = "";
    input.value = myNickname;
    input.focus();
    btn.textContent = "保存";
    isEditingNickname = true;
  } else {
    saveNickname();
  }
}

async function saveNickname() {
  const input = document.getElementById("nicknameInput");
  const val = input.value.trim();
  if (!val) { showToast("昵称不能为空", "error"); return; }

  const result = await window.friendsAPI.updateNickname({ nickname: val });
  if (result.success) {
    myNickname = result.data.nickname;
    showNicknameDisplay();
    showToast("昵称已更新", "success");
  } else {
    showToast(result.message, "error");
  }
}

function showNicknameDisplay() {
  const display = document.getElementById("nicknameDisplay");
  const input = document.getElementById("nicknameInput");
  const btn = document.getElementById("nicknameBtn");

  display.textContent = myNickname;
  display.style.display = "";
  input.style.display = "none";
  btn.textContent = "修改";
  isEditingNickname = false;
}

// --- Add Friend ---
async function addFriend() {
  const input = document.getElementById("addInput");
  const nickname = input.value.trim();
  if (!nickname) { showToast("请输入好友昵称", "error"); return; }
  const result = await window.friendsAPI.addFriend({ nickname });
  if (result.success) {
    showToast("好友请求已发送", "success");
    input.value = "";
  } else {
    showToast(result.message, "error");
  }
}

// --- Respond to Request ---
async function respondRequest(friendId, action) {
  const result = await window.friendsAPI.respondRequest({ friendId, action });
  if (result.success) {
    showToast(action === "accept" ? "已添加好友" : "已拒绝", "success");
    await loadData();
    render();
  } else {
    showToast(result.message, "error");
  }
}

// --- Remove Friend ---
async function removeFriend(friendId, event) {
  event.stopPropagation();
  if (!confirm("确定删除该好友？")) return;
  const result = await window.friendsAPI.removeFriend({ friendId });
  if (result.success) {
    showToast("已删除好友", "success");
    await loadData();
    render();
  } else {
    showToast(result.message, "error");
  }
}

// --- Load Data ---
async function loadData() {
  const [friends, pending] = await Promise.all([
    window.friendsAPI.getList(),
    window.friendsAPI.getPending(),
  ]);
  friendsData = friends;
  pendingData = pending;
}

// --- Render ---
function render() {
  const container = document.getElementById("listContainer");

  if (currentTab === "friends") {
    const online = friendsData.filter(f => f.is_online);
    const offline = friendsData.filter(f => !f.is_online);

    if (friendsData.length === 0) {
      container.innerHTML = '<div class="empty-state">暂无好友<br>在下方输入昵称添加好友吧</div>';
      return;
    }

    let html = "";
    if (online.length > 0) {
      html += '<div class="group-header" onclick="toggleGroup(this)"><span class="arrow">▼</span> 在线好友 <span class="count">(' + online.length + ')</span></div>';
      html += '<div class="group-body">';
      for (const f of online) {
        html += renderFriendItem(f);
      }
      html += '</div>';
    }
    if (offline.length > 0) {
      html += '<div class="group-header" onclick="toggleGroup(this)"><span class="arrow">▼</span> 离线好友 <span class="count">(' + offline.length + ')</span></div>';
      html += '<div class="group-body">';
      for (const f of offline) {
        html += renderFriendItem(f);
      }
      html += '</div>';
    }
    container.innerHTML = html;
  } else {
    updatePendingBadge();
    if (pendingData.length === 0) {
      container.innerHTML = '<div class="empty-state">暂无好友请求</div>';
      return;
    }
    let html = "";
    for (const f of pendingData) {
      html += '<div class="pending-item">';
      html += '  <span class="from">' + escapeHtml(f.nickname) + '</span>';
      html += '  <button class="action-btn accept" onclick="respondRequest(' + f.friend_id + ',\'accept\')">接受</button>';
      html += '  <button class="action-btn reject" onclick="respondRequest(' + f.friend_id + ',\'reject\')">拒绝</button>';
      html += '</div>';
    }
    container.innerHTML = html;
  }
}

function renderFriendItem(f) {
  const dotClass = f.is_online ? "online" : "offline";
  return '<div class="friend-item">'
    + '<div class="status-dot ' + dotClass + '"></div>'
    + '<span class="friend-nickname">' + escapeHtml(f.nickname) + '</span>'
    + '<span class="pet-name">' + (f.pet_name ? escapeHtml(f.pet_name) : "") + '</span>'
    + '<span class="remove-btn" onclick="removeFriend(' + f.friend_id + ', event)">x</span>'
    + '</div>';
}

function toggleGroup(header) {
  const arrow = header.querySelector(".arrow");
  const body = header.nextElementSibling;
  if (body && body.classList.contains("group-body")) {
    const isCollapsed = body.style.display === "none";
    body.style.display = isCollapsed ? "" : "none";
    arrow.classList.toggle("collapsed", !isCollapsed);
  }
}

function updatePendingBadge() {
  const tab = document.getElementById("requestsTab");
  if (pendingData.length > 0) {
    tab.innerHTML = '好友请求 <span class="badge">' + pendingData.length + '</span>';
  } else {
    tab.textContent = '好友请求';
  }
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

// --- Auto Refresh ---
async function refreshData() {
  if (isEditingNickname) return;
  await loadData();
  updatePendingBadge();
  render();
}

// --- Init ---
(async function init() {
  const me = await window.friendsAPI.getMe();
  if (me.success) {
    myNickname = me.data.nickname;
    document.getElementById("nicknameDisplay").textContent = myNickname;
  }
  await loadData();
  updatePendingBadge();
  render();
  refreshTimer = setInterval(refreshData, REFRESH_MS);
})();
