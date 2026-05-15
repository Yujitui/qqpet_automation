# QQ宠物社交功能需求说明书

## 1. 全局基础需求
* **关系链支持**：程序需接入统一的用户好友关系链（如模拟 QQ 好友列表）。
* **唯一标识符**：每只宠物需具备全局唯一 ID，并与持有者的账号（UIN）绑定。
* **状态同步引擎**：需引入实时通信机制（如 WebSockets 或长轮询），确保跨客户端的动作（如做客、求婚）能实时推送到对方桌面。

---

## 2. 结婚系统 (Marriage System)

### 2.1 基础条件与限制
* **属性校验**：校验双方宠物是否达到法定等级（如 15 级）、性别是否异性、当前婚姻状态是否为“未婚”。
* **道具消耗**：发起求婚的一方背包中必须拥有“结婚戒指”道具。

### 2.2 核心业务流程
* **求婚发起**：玩家 A 选择好友 B 的宠物，点击“求婚”，扣除戒指道具，向服务器发送求婚请求。
* **求婚推送与响应**：服务器向玩家 B 客户端推送弹窗通知。玩家 B 可选择“接受”或“拒绝”。
* **超时处理**：设置求婚响应倒计时（如 2 分钟），超时自动判定为拒绝，并退回/不退回道具。
* **状态更新**：接受后，服务器更新双方宠物元数据（婚姻状态改为已婚、写入配偶 ID、初始化亲密度为 0）。

### 2.3 前端表现与视觉
* **婚礼动效**：双方同意后，两台电脑桌面上同步播放特定的婚礼全屏/局部动画。
* **特殊标识**：宠物个人面板新增“配偶姓名”字段，并解锁“结婚证”道具查看功能。

### 2.4 持续互动（亲密度）
* **数值设计**：新增“夫妻亲密度”属性。
* **增长触发**：每日首次共同在线、互相赠送特定道具、互相喂食可增加固定亲密度。

---

## 3. 生育系统 (Breeding System)

### 3.1 基础条件与限制
* **前置条件**：宠物状态必须为“已婚”，且夫妻亲密度需达到指定阈值。
* **冷却时间 (CD)**：设置生育冷却期（如真实时间 7 天内只能生育一次），防止宠物蛋泛滥。

### 3.2 核心业务流程
* **触发机制**：满足条件后，由任意一方（或双人在线时触发）向服务器发起“求子/生蛋”请求。
* **产蛋逻辑**：服务器判定成功后，生成一枚“宠物蛋”数据对象，其基因（如颜色、初始资质）基于父母双方的属性随机生成。
* **所有权分配**：默认第一只蛋归属于发起方，或直接生成两枚蛋，夫妻各得一枚。
* **孵化与赠送**：
  * **孵化期**：宠物蛋需在背包中倒计时（如 24 小时）或需要通过点击“抚摸”累积孵化值。
  * **转赠逻辑**：未孵化的蛋允许玩家直接定向赠送给关系链中的“未养宠好友”。

### 3.3 前端表现与视觉
* **生蛋动画**：桌面宠物触发“下蛋/送子鸟”的逗趣特效动画。
* **物品图标**：背包中新增动态的“宠物蛋”物品图标。

---

## 4. 做客系统 (Visiting System)

### 4.1 基础条件与限制
* **状态限制**：宠物在生病、濒死、打工、上学状态下无法出门做客。
* **同屏限制**：单个玩家的桌面同时容纳的“访客宠物”需设上限（如最多 3 只）。

### 4.2 核心业务流程
* **派遣阶段**：玩家 A 在好友列表中选择在线的玩家 B，点击“去串门”。玩家 A 的桌面宠物消失或进入“外出”状态。
* **跨端呈现**：服务器将宠物 A 的外观数据、当前状态打包发送给玩家 B 的客户端，宠物 A 随即在玩家 B 的电脑桌面上渲染渲染。
* **桌面互动逻辑**：
  * **自主行为**：访客宠物在他人桌面上出现，并触发特定文本气泡（如“来偷吃啦！”）。
  * **主人接待**：玩家 B 可以对访客宠物进行“喂食”、“洗澡”，消耗玩家 B 的道具，但会提升宠物 A 的属性。
  * **惩罚/驱逐**：若访客宠物触发捣乱事件，玩家 B 可点击“驱逐”，立即结束做客行为。
* **返回机制**：做客设有时间上限（如 30 分钟），超时或被驱逐后，触发返回逻辑，宠物 A 重新回到玩家 A 的桌面，并带回做客收益（如经验值）。

### 4.3 前端表现与视觉
* **多实例渲染**：客户端动画引擎需支持同时渲染、控制多个不同 ID 宠物的动画状态机。

---

## 5. 补充资源 — 原版动画资产（assets/show/）

从原版 QQ 宠物资源中提取并重新整理的动画文件，位于项目根目录 `assets/show/`。

### 5.1 文件结构

每个动画包含两个文件：`<名称>.gif`（缩略图预览）和 `<名称>.swf`（Flash 动画）。动画分为 GG（男宠）和 MM（女宠）两个版本，共 **162 个独立动画 × 2 格式（GIF+SWF） = 324 文件**。

### 5.2 分类目录

#### 核心社交动画

| 动画 | GG | MM | 用途 |
|------|----|----|------|
| `proposal` | ✅ | ✅ | 求婚动作 |
| `receive_love` | ✅ | ✅ | 收到示爱反应 |
| `expressing_love` | ✅ | ✅ | 表白动画 |
| `expressing_love_but_rejected` | ✅ | ❌ | 示爱被拒（GG 独有） |
| `expressing_love_and_accept` | ❌ | ✅ | 接受表白（MM 独有） |
| `shame` | ✅ | ✅ | 害羞捂脸 |
| `shocked` | ✅ | ✅ | 震惊 |
| `missing_lover` | ✅ | ✅ | 思念爱人 |
| `asking_for_date` | ✅ | ✅ | 约会邀请 |
| `dating_interrupted` | ✅ | ✅ | 约会被打扰 |
| `anthomaniac` | ✅(2) | ✅(1) | 花痴状态 |
| `chinese_new_year_with_lover` | ✅ | ❌ | 与爱人过年（GG 独有） |

#### 情侣互动动画

| 动画 | GG | MM | 用途 |
|------|----|----|------|
| `interactions_between_lovers_1~N` | ✅(20) | ✅(22) | 日常情侣互动（拥抱、依偎等） |
| `interactions_between_lovers_with_X_sick` | ✅(GG 病) | ✅(MM 病) | 一方生病时的互动 |
| `happy_birthday_to_X` | ✅(to MM) | ✅(to GG) | 为对方庆祝生日 |
| `love_to_player` | ✅(2) | ✅(2) | 宠物对主人表达爱意 |

#### 情绪/表情动画

`laugh`(笑)、`cry`(哭)、`angry`(生气)、`funny`(搞笑)、`stunned`(发懵)、`question`(疑惑)、`remind`(提醒)、`warn`(警告)、`dizziness`(头晕)

#### 日常生活动画

`celebrate`(庆祝)、`go_to_work`(工作)、`eat_boxed_lunch`(便当)、`hungry`(饿)、`shower`(洗澡)、`sleep`(睡觉)、`sleepy`(困)、`vomit`(呕吐)、`tickle`(挠痒)、`play_game`(玩游戏)

#### 表演动画

`show_off` 炫耀表演（GG 9 个、MM 8 个）、`chinese_new_year` 新年庆祝（各 10 个）

### 5.3 关键设计约束

1. **所有动画均为单宠动画** — 即使表现双宠互动，首帧也仅为单宠正面画面
2. **双宠交互需拼接实现** — 在画面中同时运行两个 Ruffle 实例，分别加载 GG 和 MM 的独立动画，时间轴对齐以呈现互动效果
3. **音频资源配合** — `jh.mid`（婚礼 BGM）、`yes.wav`（接受音效）、`no.wav`（拒绝音效）可配合动画触发
4. **原版其他资源已清理** — 无需的 bing/chi/qingjie/work/zs/qgg/qmm/zgg/zmm 目录已删除，根目录仅保留 `assets/show/`

---

## 6. 多阶段实施计划

基于现有资源和架构，社交功能分 6 个阶段实施，按依赖关系排序：

```
阶段 1：基础设施 ✅ → 阶段 2：好友系统 ✅ → 阶段 3：做客系统 → 阶段 4：结婚系统 → 阶段 5：生育系统 → 阶段 6：优化
                                    ↕                          ↕
                            多宠物同屏渲染能力           婚礼 = 临时非交互做客（复用做客系统）
```

### 阶段 1：基础设施 — WebSocket 框架 + 社交数据层

> ✅ **1.1 WebSocket 实时通信框架 — 已实现**（2026-05-15）
> 服务端：ConnectionManager + JWT 认证 + 消息路由（system/sync/social）
> 客户端：wsClient.js 通用框架 + RemoteStore WS 推送接收 + 自动重连
> 集成：main.js 启动连接，注销/踢出断开

##### 1.1.1 架构概览

```
┌─────────────────────┐         ┌──────────────────────────┐
│   Electron 客户端      │         │     FastAPI 服务端           │
│                      │         │                          │
│  ┌───────────────┐   │  HTTP   │  ┌────────────────────┐  │
│  │  api.js       │──┼─────────┼─▶│  REST API 端点       │  │
│  │  (HTTP 读写)   │   │         │  │  (读取/写入，过渡期)  │  │
│  └───────────────┘   │         │  └────────────────────┘  │
│                      │         │                          │
│  ┌───────────────┐   │  WS     │  ┌────────────────────┐  │
│  │  wsClient.js  │──┼─────────┼─▶│  /ws 端点            │  │
│  │  (通用框架)    │   │         │  │  ConnectionManager  │  │
│  └───────┬───────┘   │         │  │  MessageRouter      │  │
│          │           │         │  └────────────────────┘  │
│          ▼           │         └──────────────────────────┘
│  ┌───────────────┐   │
│  │  remoteStore  │   │
│  │  改造接收推送   │   │
│  └───────────────┘   │
└─────────────────────┘
```

**双轨并行策略**：
- **写入**：先保留 HTTP PATCH（`remoteStore.scheduleSync()`），稳定后迁移至 WS
- **推送**：服务端数据变更通过 WS 推送 → RemoteStore 更新缓存
- **读取**：HTTP GET 不变

##### 1.1.2 消息协议

所有消息统一格式：

```json
{
  "router": "sync.pet",
  "action": "update",
  "data": {},
  "id": "a1b2c3d4",
  "from": 1,
  "to": null,
  "timestamp": 1715000000000
}
```

| 字段 | 说明 | 示例 |
|------|------|------|
| `router` | 路由名称，`.` 分层 | `sync.pet`、`social.proposal`、`system.heartbeat` |
| `action` | 操作类型 | `update`、`request`、`response`、`notify`、`error` |
| `data` | 业务数据负载 | `{}` |
| `id` | UUID（请求-响应匹配） | `"a1b2c3"` |
| `from` | 发送者用户 ID | `1` |
| `to` | 目标用户 ID（可选） | `2` 或 `null` |
| `timestamp` | Unix 毫秒时间戳 | `1715000000000` |

##### 1.1.3 服务端设计

**目录结构**：
```
server/app/ws/
├── __init__.py
├── manager.py       # ConnectionManager — 连接池 + 用户映射
├── handler.py       # 消息分发（按 router 字段路由）
└── auth.py          # JWT 认证（首次连接验证 token）
```

**ConnectionManager 核心能力**：
- `connect(ws, user_id)` — 注册连接，建立 user_id → WebSocket 映射
- `disconnect(ws)` — 断开清理，更新在线状态
- `send_to_user(user_id, message)` — 点对点推送
- `broadcast(message)` — 广播（预留）
- `get_online_users()` — 获取在线用户列表
- `is_online(user_id)` — 检查用户是否在线

**消息路由机制**：
```
ws.on_message
  → decode JSON
  → verify JWT (首次连接时验证)
  → router dispatch:
      "sync.*"     → SyncHandler (数据同步)
      "social.*"  → SocialHandler (社交推送)
      "system.*"  → SystemHandler (心跳、连接管理)
```

**认证方式**：
```
连接 URL: ws://localhost:8000/ws?token=<jwt_access_token>
```
首次连接时将 JWT token 作为 query parameter 传递，服务端验证后建立连接。后续消息不再重复验证。

**HTTPS 适配**（无损）：
- 客户端 URL 自动推导：`http` → `ws`，`https` → `wss`
- 服务端路径 `/ws` 不变，SSL 由 uvicorn 或反向代理（nginx）配置
- 应用层代码零改动

##### 1.1.4 客户端设计

**新增文件**：`qq-pet-macos/src/network/wsClient.js`

```javascript
class WSClient {
  async connect(url, token)         // 建立连接
  disconnect()                      // 主动断开
  send(router, action, data)        // 发送消息（fire-and-forget）
  async request(router, action,     // 请求-响应模式（含超时）
                data, timeout)
  on(router, callback)              // 注册消息监听
  off(router, callback)             // 移除监听
  onOpen, onClose, onError          // 连接事件回调
}
```

**自动重连机制**：
- 首次重连等待 1 秒
- 后续指数退避：1s → 2s → 4s → 8s（最大 30 秒）
- Token 过期检测：收到 401 时触发 `global.onAuthRequired`

**位置**：放在 `network/` 目录（主进程），与 `api.js` 同级，直接访问 auth token。

##### 1.1.5 RemoteStore 整合

**当前状态**：写入优先走 WS，失败后 HTTP 兜底

```
数据同步流程：

  setItem(key, value)
    → cache 更新
    → scheduleSync()
        1. WS request("sync.pet", "update", data, 3000) ← 优先
        2. 成功 → ack 确认，完成
        3. 失败/超时 → HTTP PATCH 兜底（原有逻辑）
```

**推送接收**（不变）：

```
  WS 收到 "sync.*" 消息
    → RemoteStore 更新本地 cache
    → 触发 UI 刷新
```

##### 1.1.6 实施子步骤与验证目标

**子步骤**：

| 子步骤 | 内容 | 估时 | 状态 |
|--------|------|------|------|
| 1a | 服务端 ConnectionManager + `/ws` 端点 | 半天 | ✅ |
| 1b | 服务端消息路由（按 router 分发）+ JWT 认证 | 半天 | ✅ |
| 1c | 客户端 `wsClient.js` 通用框架（连接/发送/监听） | 半天 | ✅ |
| 1d | 客户端 `remoteStore.js` 集成 WS 推送接收 | 半天 | ✅ |
| 1e | 心跳 + 断线重连 + Token 过期处理 | 半天 | ✅ |
| 1f | 验收测试：连接认证、消息收发、重连恢复 | 半天 | ✅ |
| 1g | `syncPending()` 改造：WS 优先写入 + HTTP 兜底 | 半天 | ✅ |

**验证目标**：

| # | 验证项 | 验收标准 | 状态 |
|---|--------|---------|------|
| V1a | 服务端连接认证 | 传入有效 JWT → 连接成功；无效 JWT → 拒绝连接 | ✅ |
| V1b | 消息路由 | 发送 `system.ping` → 回复 `system.pong` | ✅ |
| V1c | 客户端连接 | `wsClient.connect()` 成功后 `onOpen` 触发 | ✅ |
| V1d | 客户端收发 | `wsClient.send()` 服务端可收到；服务端推送客户端可收到 | ✅ |
| V1e | 请求-响应模式 | `wsClient.request()` → 正确返回 | ✅ |
| V1f | 自动重连 | 断开服务端后，客户端在 30 秒内自动恢复 | ✅ |
| V1g | RemoteStore 推送 | WS 推送 `sync.*` → RemoteStore 缓存更新 | ✅ |
| V1h | 心跳保活 | 连接空闲时不因超时断开 | ✅ |
| V1i | WS 优先写入 + HTTP 兜底 | WS 在线时用 `wsClient.request()` 同步；WS 离线时自动回退到 HTTP PATCH | ✅ |
| V1j | JSON 列变更跟踪（Bug 修复） | HTTP PATCH + WS 写入的库存数据持久化到数据库 | ✅ |

**小计**：约 3 天（1.1 已完成）

#### 1.2 社交数据层

##### 1.2.1 宠物唯一标识

当前 `pet_data` 仅有内部 `id`（PK）和 `user_id`（FK），**无对外公开标识**。

**改造**：新增 `public_uid` 字段，`VARCHAR(12)`，作为宠物的对外身份证号。用途：
- 好友间引用对方宠物（如"查看某某的宠物"）
- 婚姻关系中的配偶标识
- 做客系统的访客标识

```
格式：uuid.uuid4().hex[:12]  — 12 位 hex，URL 友好
```

```
宠物重置时 → 生成新 public_uid → 旧关联由 PetMarriages 记录追溯
```

##### 1.2.2 数据模型设计

**PetData 扩展（原有字段不变，新增以下）**

```sql
pet_data:
  -- 新增 --
  public_uid        VARCHAR(12) UNIQUE NOT NULL   -- 公开唯一标识
  marriage_status   VARCHAR(20) DEFAULT 'single'  -- single / married / widowed
  spouse_uid        VARCHAR(12) NULL              -- 配偶的 public_uid
  intimacy          INTEGER DEFAULT 0             -- 当前亲密度
```

**Friends（用户级好友，稳定）**

```sql
friends:
  id              SERIAL PK
  user_id         INTEGER FK → users.id          -- 发起方
  friend_user_id  INTEGER FK → users.id          -- 接收方
  status          VARCHAR(20) DEFAULT 'pending'  -- pending / accepted / blocked
  created_at      TIMESTAMP
  updated_at      TIMESTAMP
  UNIQUE(user_id, friend_user_id)
```

> 基于用户而非基于宠物，好友关系不受宠物重置影响。

**PetMarriages（婚姻历史，不可变）**

```sql
pet_marriages:
  id              SERIAL PK
  pet_a_uid       VARCHAR(12) NOT NULL            -- 配偶 A 的 public_uid
  pet_b_uid       VARCHAR(12) NOT NULL            -- 配偶 B 的 public_uid
  user_a_id       INTEGER FK → users.id           -- 便于按用户查询
  user_b_id       INTEGER FK → users.id           -- 便于按用户查询
  status          VARCHAR(20) DEFAULT 'active'    -- active / divorced / widowed / annulled
  intimacy        INTEGER DEFAULT 0
  married_at      TIMESTAMP
  ended_at        TIMESTAMP NULL
```

> `pet_a_uid` / `pet_b_uid` 不设 FK 约束（重置时旧 uid 自动失效）。

##### 1.2.3 宠物重置时的关系处理

```
用户 A 调用 initPet({reset: true})
  → 查出旧 pet_data.public_uid
  → 查询 pet_marriages WHERE (pet_a_uid OR pet_b_uid) = old_uid AND status = 'active'
  → 若有 → 设 status='widowed'，ended_at=now
  → 对方 pet_data.marriage_status 改为 'widowed'
  → [待实现] 通过 WS 推送通知对方用户
  → 硬删除旧 pet_data + inventory（user_id 唯一约束）
  → 创建新 pet_data + inventory，public_uid = uuid4().hex[:12]
```

> **保持硬删除**：不引入 `is_disabled` 软删除，简化变更集。婚姻历史由 `PetMarriages` 表记录，可供追溯。

##### 1.2.4 后续 API 端点（待各阶段实现）

| 阶段 | 端点 | 说明 | 状态 |
|------|------|------|------|
| 2 | `GET/POST /api/friends` | 好友列表 + 添加好友 | ✅ |
| 2 | `PATCH/DELETE /api/friends/{id}` | 接受/拒绝/删除 | ✅ |
| 3 | `POST /api/visit` | 发起做客 | ⏳ |
| 3 | `PATCH /api/visit/{id}/respond` | 接受/驱逐访客 | ⏳ |
| 4 | `POST /api/marriage/propose` | 求婚 | ⏳ |
| 4 | `PATCH /api/marriage/{id}/respond` | 接受/拒绝求婚 | ⏳ |

**依赖**：无  
**工作量**：小（3-4 小时）

> ✅ **1.2 社交数据层 — 已实现**（2026-05-15）
> ORM/Pydantic/SQL 三路同步完成，8 项验证全部通过。

##### 1.2.5 实施子步骤

| 子步骤 | 文件 | 内容 | 状态 |
|--------|------|------|------|
| 1.2a | `models/pet.py` | PetData 新增 `public_uid`、`marriage_status`、`spouse_uid`、`intimacy` | ✅ |
| 1.2b | `models/friend.py` | 新建 Friend 模型 | ✅ |
| 1.2c | `models/marriage.py` | 新建 PetMarriage 模型 | ✅ |
| 1.2d | `models/__init__.py` + `database.py` + `main.py` | 注册新模型到 `init_db()` | ✅ |
| 1.2e | `schemas/pet.py` | PetDataResponse 扩展（social 字段） | ✅ |
| 1.2f | `initdb.d/001_init_schema.sql` | 同步 DDL（pet_data 扩展 + friends + pet_marriages） | ✅ |
| 1.2g | `api/pet.py` | `pet_data_to_response` 扩展 + `init_pet` reset 流程改造 + `public_uid` 生成 | ✅ |
| 1.2h | 测试 | 验证 public_uid 生成、reset 后婚姻记录正确处理 | ✅ |

##### 1.2.6 验证目标

| # | 验证项 | 验收标准 | 状态 |
|---|--------|---------|------|
| V1.2a | PetData 新增列 | `pet_data` 表含 `public_uid`（UNIQUE NOT NULL）、`marriage_status`、`spouse_uid`、`intimacy` | ✅ |
| V1.2b | friends 表 | `friends` 表存在，含 `user_id`、`friend_user_id`、`status`、唯一约束 `(user_id, friend_user_id)` | ✅ |
| V1.2c | pet_marriages 表 | `pet_marriages` 表存在，含 `pet_a_uid`、`pet_b_uid`、`user_a_id`、`user_b_id`、`status` | ✅ |
| V1.2d | public_uid 自动生成 | `POST /api/pet/init` 返回的响应含非空 `public_uid`，格式为 12 位 hex | ✅ |
| V1.2e | GET /api/pet 返回社交字段 | `GET /api/pet` 返回 `public_uid`、`marriage_status`、`spouse_uid`、`intimacy` | ✅ |
| V1.2f | Reset 生成新 uid | `initPet({reset:true})` 后 `public_uid` 与前次不同 | ✅ |
| V1.2g | Reset 标记婚姻 widowed | Reset 时若有活跃婚姻 → `pet_marriages.status` 改为 `widowed`，对方 `marriage_status` 改为 `widowed` | ✅ |
| V1.2h | DDL 一致性 | SQLAlchemy ORM 列定义与 `001_init_schema.sql` 完全一致 | ✅ |

---

### 阶段 2：好友系统 ✅

> ✅ **完整实现**（2026-05-15）
> 昵称系统 + 好友 API + 前端弹窗 + WS 推送 + 右键菜单集成。12 项后端验证 + 全部前端验收通过。

#### 2.0 昵称系统（好友前置依赖）

> 当前用户仅有 `username`（登录用），社交展示需要独立昵称。**[已实现]**

##### 2.0.1 数据模型

`users` 表新增：
```sql
nickname VARCHAR(50) UNIQUE NOT NULL,
CREATE INDEX IF NOT EXISTS idx_users_nickname ON users(nickname);
```

`User` ORM 模型对应新增 `nickname` 列。注册时默认 `nickname = username`。

##### 2.0.2 API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| `PATCH` | `/api/auth/nickname` | 修改昵称（含去重检查 → 409） |
| — | `POST /api/auth/register` | 支持可选 `nickname` 字段，默认=`username` |

已有 `GET /api/auth/me` 和 `POST /api/auth/login` 响应中自动包含 `nickname`。

##### 2.0.3 前端改动

- `network/api.js` 新增 `updateNickname(nickname)`
- 好友窗口顶部显示自己昵称 + 编辑按钮（内联编辑）

##### 2.0.4 验证目标

| # | 验证项 | 验收标准 | 状态 |
|---|--------|---------|------|
| V0a | 注册默认昵称 | 新用户 `nickname` = `username`，唯一 | ✅ |
| V0b | 修改昵称 | `PATCH` 成功后 `GET /me` 返回新昵称 | ✅ |
| V0c | 昵称去重 | 重复昵称 → 409 | ✅ |
| V0d | 空昵称拒绝 | 空/纯空白 → 400 | ✅ |
| V0e | 好友搜索 | `POST /api/friends` 按 `nickname` 查找（见 V3a） | ✅ |

**依赖**：阶段 1（基础设施）  
**工作量**：小（1-2 小时） — 已实现

---

#### 2.1 后端 API — 已实现

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/friends` | 好友列表（含在线状态，通过 WS ConnectionManager） |
| `GET` | `/api/friends/pending` | 待处理好友请求 |
| `POST` | `/api/friends/add` | 按 `nickname` 发送好友请求 |
| `POST` | `/api/friends/{id}/respond` | 接受/拒绝好友请求（`action: accept/reject`） |
| `DELETE` | `/api/friends/{id}` | 删除好友 |

- 好友列表按 `nickname` 搜索添加（昵称模糊匹配，支持大小写不敏感）
- 在线状态：通过 ConnectionManager 获取对方在线状态并返回列表
- 重复请求检测：已发送/已是好友 → 409 Conflict

#### 2.2 前端 — 已实现

**右键菜单集成**：
- 右键菜单新增"好友"子菜单 → "打开好友列表"
- 右键菜单替换已重构为按 `value` 字段标识（`l(targetValue, newItem)`），替代原硬编码数组索引

**独立弹窗** `windows/popups/friends/`：
- `main.js` — BrowserWindow 创建 + IPC handlers（`getMe`、`getFriends`、`addFriend`、`respondFriend`、`deleteFriend`、`updateNickname`）
- `preload.js` — IPC bridge（contextBridge 暴露 API）
- `index.html` — QQ 2006-2010 风格 UI
- `index.js` — 逻辑层（昵称内联编辑、好友列表渲染、请求列表、折叠分组）

**好友窗口功能**：
- 顶部显示自己昵称 + "修改"按钮（点击切换为输入框 + "保存"，保存后立即刷新显示文本）
- 分组折叠：我的好友（在线/离线）/ 好友请求（收到/发出）
- 在线状态实时显示（绿色 `#00CC00` 圆点 / 灰色 `#AAAAAA` 圆点）
- **定时自动刷新**：每 10 秒自动轮询好友列表和请求数据，窗口关闭时自动停止
- **编辑时暂停刷新**：编辑昵称期间跳过自动刷新，避免干扰用户输入
- 好友请求接受/拒绝按钮 + 删除好友

#### 2.3 设计风格（QQ 2006-2010）— 已实现

| 元素 | 规范 |
|------|------|
| 标题栏 | `linear-gradient(#0757D9, #0650CC)`，白色 12px 粗体文字 |
| 窗口背景 | `#E8F0FE` |
| 列表项 hover | `#C6DAF5` |
| 在线指示 | 绿色 `#00CC00` 圆点 / 灰色 `#AAAAAA` 圆点 |
| 分组标题 | `#6699CC` 粗体，可折叠 |
| 窗口尺寸 | 280 × 440，frameless，置顶 |

#### 2.4 WebSocket 集成 — 已实现

| router | action | 说明 |
|--------|--------|------|
| `social.friend_online` | `update` | 好友上线/下线推送 |
| `social.status_broadcast` | `update` | 广播在线状态（收到后更新在线好友列表） |

- **实际推送 endpoint**：`social.friend_online`（`update`）+ `social.status_broadcast`（`update`）
- WS `social.friend_request` / `social.friend_response` 预留，待 Phase 3 加强通知体验
- 当前好友请求通过 HTTP API 完成，在线状态通过 WS 实时更新

**依赖**：阶段 1（基础设施、WebSocket）、阶段 2.0（昵称系统）  
**工作量**：中（后端：1-2 天，前端：2-3 天） — 已实现

**实施子步骤**：

| 子步骤 | 文件 | 内容 | 状态 |
|--------|------|------|------|
| N1 | `models/user.py` + SQL DDL + Schema | User 模型新增 `nickname VARCHAR(50) UNIQUE` | ✅ |
| N2 | `api/auth.py` + `schemas/auth.py` | `PATCH /api/auth/nickname` 端点（空→400/重复→409/成功→200） | ✅ |
| 2a | `api/friend.py` + `schemas/friend.py` | 好友 API 完整实现（5 个端点） | ✅ |
| 2b | `network/api.js` | `updateNickname()` + 6 个好友方法（getFriends/getPending/addFriend/respondFriend/deleteFriend/findUsersByNickname） | ✅ |
| 2c | `windows/popups/friends/main.js` + `preload.js` | 好友窗口框架（BrowserWindow + IPC bridge） | ✅ |
| 2d | `windows/popups/friends/index.html` + `index.js` | QQ 2006 风格 UI + 完整交互逻辑（含 10 秒自动刷新 + 编辑时暂停） | ✅ |
| 2e | `windows/popups/rightMenu/index.js` + `main.js` | 右键菜单"好友"入口 + value 替换重构 | ✅ |
| 2f | `ws/handler.py` + `ws/manager.py` | `social.friend_online` / `social.status_broadcast` WS 推送 | ✅ |
| 2g | Docker 重启验证 | 全部 12 项后端测试通过 + 前端语法校验 | ✅ |

**验证目标**：

| # | 验证项 | 验收标准 | 状态 |
|---|--------|---------|------|
| V3a | 发送好友请求 | 用户 A 按 `nickname` 向 B 发送请求 → DB `friends.status = 'pending'` | ✅ |
| V3b | 接受/拒绝好友 | B 接受 → `accepted`；B 拒绝 → 记录删除或 `blocked` | ✅ |
| V3c | 删除好友 | 已存在好友可删除，双方同步移除 | ✅ |
| V3d | 在线状态指示 | 好友列表中在线用户显示绿色点，离线灰色 | ✅ |
| V3e | 好友列表 UI | QQ 2006 风格：蓝白配色、分组折叠、可滚动列表 | ✅ |
| V3f | WS 通知 | 好友上线/下线通过 WS 实时推送，好友列表自动更新 | ✅ |
| V3g | 昵称搜索 | 按昵称模糊搜索添加好友，大小写不敏感 | ✅ |
| V3h | 重复请求检测 | 已发送好友请求不可重复发送 → 409 Conflict | ✅ |
| V3i | 右键菜单入口 | 右键菜单 → 好友 → 打开好友列表，窗口正常弹出 | ✅ |
| V3j | 昵称编辑 | 好友窗口顶部内联修改昵称，保存后即时刷新 | ✅ |
| V3k | 分组折叠 | 我的好友/好友请求分组可折叠展开 | ✅ |
| V3l | 空好友列表 | 无好友/无请求时显示对应空状态提示 | ✅ |
| V3m | 定时自动刷新 | 好友窗口打开后每 10s 自动刷新好友列表和请求数据，编辑昵称时跳过刷新 | ✅ |

---

### 阶段 3：做客系统 ← 核心攻坚

**后端**：
- 做客 API（派遣、接收、驱逐、返回）
- 访客状态管理 + 超时自动返回（如 30 分钟）

**前端**：
- **多 Ruffle 实例同屏渲染**（最核心的工程挑战）
- 访客宠物 AI 行为逻辑（自主行走、气泡对话）
- 主人互动按钮（喂食、洗澡、驱逐）
- 派遣和返回动效

**依赖**：阶段 2（好友列表）  
**工作量**：非常大（后端：2 天，前端架构改造：3-5 天，AI 行为：2-3 天）

**设计要点**：
- 做客系统的多宠物同屏能力是后续结婚系统的技术基础
- 结婚场景将被实现为"临时的、非交互的做客"
- 此阶段的架构设计需预留扩展接口给结婚仪式使用

**验证目标**：

| # | 验证项 | 验收标准 |
|---|--------|---------|
| V4a | 派遣做客 | 用户 A 选择好友 B 点击"去串门"→ A 的宠物消失，进入"外出"状态 |
| V4b | 跨端呈现 | B 的桌面上出现 A 的宠物动画，位置坐标正确 |
| V4c | 双宠同屏 | B 自己的宠物 + A 的访客宠物同时出现在桌面上，互不干扰 |
| V4d | 主人互动 | B 可对访客进行喂食/洗澡，消耗 B 的道具，增加 A 的属性 |
| V4e | 驱逐访客 | B 点击驱逐 → 访客立即消失，A 的宠物返回桌面 |
| V4f | 超时自动返回 | 30 分钟后访客自动返回，A 的宠物重新出现 |
| V4g | 状态限制 | 生病/打工/上学中的宠物不可作为访客派遣 |
| V4h | 同屏上限 | 最多 3 只访客同时在场，第 4 只被拒绝 |

---

### 阶段 4：结婚系统

**后端**：
- 婚姻 API：发起求婚、响应（接受/拒绝）、超时处理
- 戒指道具校验 + 扣除逻辑
- 亲密度增长逻辑（每日共同在线、互赠道具等）

**前端**：
- 好友列表中的"求婚"按钮
- 求婚弹窗通知（接收方） + 倒计时
- **婚礼场景 = 临时的非交互做客**：直接复用阶段 3 的"双宠同屏"能力
- 宠物面板显示配偶信息
- 结婚证道具/面板

**依赖**：阶段 3（做客系统 = 多宠物同屏能力 + WebSocket 推送）  
**工作量**：中（后端：2-3 天，前端动画组合：1-2 天，UI：2 天）

**设计要点**：
- 求婚成功后，发起方自动向接收方发起"特殊做客"（婚礼）
- 婚礼期间双方宠物不可交互（无喂食/洗澡/驱逐按钮）
- 双方桌面同步播放婚礼动画序列：
  - GG：`gg_proposal.swf`（求婚）
  - MM：`mm_receive_love.swf` + `mm_expressing_love_and_accept.swf`（接受）
  - 双方：`gg_celebrate.swf` + `mm_celebrate.swf`（庆祝）
  - 可选：`jh.mid`（婚礼 BGM）
- 婚礼结束后自动返回正常状态

**验证目标**：

| # | 验证项 | 验收标准 |
|---|--------|---------|
| V5a | 求婚发起 | A 持有戒指道具，向好友 B 求婚 → 扣除戒指，B 收到推送通知 |
| V5b | 接受求婚 | B 接受 → 双方 `marriage_status` 改为 `married`，`pet_marriages` 写入 |
| V5c | 拒绝求婚 | B 拒绝 → 道具退回/不退回，状态不变 |
| V5d | 超时处理 | 2 分钟未响应 → 自动拒绝，道具退回 |
| V5e | 婚礼动画 | 双方桌面同步播放婚礼动画序列（proposal + receive + celebrate） |
| V5f | 配偶显示 | 宠物面板显示配偶名称 + 结婚日期 |
| V5g | 亲密度增长 | 每日共同在线/互赠道具后亲密度增加 |
| V5h | 恋爱状态限制 | 已婚者不可再求婚，不能与同性结婚 |

---

### 阶段 5：生育系统

**后端**：
- 生育 API（求子/生蛋/孵化）
- 宠物蛋数据模型 + 冷却时间管理（如 7 天 CD）
- 基因遗传算法（从父母属性随机生成子代资质）

**前端**：
- 背包中宠物蛋的显示与交互
- 孵化倒计时/抚摸累积孵化值
- 宠物蛋赠送 UI

**依赖**：阶段 4（婚姻状态 + 亲密度）  
**工作量**：中（后端：2-3 天，前端：2-3 天）

**验证目标**：

| # | 验证项 | 验收标准 |
|---|--------|---------|
| V6a | 求子触发 | 已婚 + 亲密度达标 + CD 已过 → 生蛋请求成功 |
| V6b | 冷却限制 | 7 天内不可重复生育 |
| V6c | 基因遗传 | 子代初始资质基于父母属性随机生成，在合理范围内 |
| V6d | 孵化倒计时 | 背包中宠物蛋显示剩余孵化时间（24 小时）或孵化值 |
| V6e | 抚摸孵化 | 点击宠物蛋累积孵化值，满值后自动孵化 |
| V6f | 赠送宠物蛋 | 未孵化的蛋可赠送给好友 |
| V6g | 生蛋动画 | 触发生蛋时播放对应动画 |

---

### 阶段 6：集成与优化

- 跨系统集成测试（结婚 → 生育 → 做客链路）
- 边缘情况处理（离婚、宠物死亡后的继承、跨天逻辑）
- 性能优化（多宠物渲染、网络延迟处理）
- 国际化（现有界面是中文，保持一致）

**依赖**：阶段 3-5  
**工作量**：中（3-5 天）

**验证目标**：

| # | 验证项 | 验收标准 |
|---|--------|---------|
| V7a | 全链路集成 | 结婚 → 生育 → 做客链路走通，状态流转正确 |
| V7b | 边缘情况 | 离婚后宠物可再婚；宠物重置后婚姻自动标记 widowed |
| V7c | 性能基准 | 单人 5 个 Ruffle 实例同时渲染时 FPS ≥ 30 |
| V7d | 网络异常 | 断网重连后所有状态与服务器一致 |
| V7e | 数据一致性 | 无孤儿数据、无悬挂引用 |

---

### 总体预估

| 阶段 | 预估天数 | 风险等级 | 状态 |
|------|---------|---------|------|
| 阶段 1：基础设施 | 5-8 天 | 🟢 低 | ✅ |
| 阶段 2：好友系统（含昵称系统） | 4-6 天 | 🟢 低 | ✅ |
| 阶段 3：做客系统 | 7-10 天 | 🔴 高（多宠物渲染架构改造） | ⏳ |
| 阶段 4：结婚系统 | 5-7 天 | 🟡 中（动画组合需调试） | ⏳ |
| 阶段 5：生育系统 | 4-6 天 | 🟢 低 | ⏳ |
| 阶段 6：集成优化 | 3-5 天 | 🟡 中 | ⏳

**总计**：约 28-41 个工作日

---

## 开发辅助修改（上线前必须还原）

以下是为开发便利所做的临时变更，**上线前必须逐项确认还原**：

| 文件 | 原代码 | 临时修改 | 还原条件 |
|------|--------|---------|---------|
| `server/app/api/auth.py:49` | `is_active=False` | 移除 `is_active`（模型默认 `True`） | ==**上线前必须还原**==，否则注册用户无需激活即可登录 |
| `server/app/api/auth.py:71` | `is_active=False` | 同上（auto-create 路径） | ==**同上**== |

### 还原操作

```python
# 1. register 路径 — server/app/api/auth.py ~line 46-49
user = User(
    username=form_data.username,
    email=form_data.email,
    hashed_password=hashed_password,
    is_active=False,   # ← 恢复为 False
    is_admin=False
)

# 2. auto-create 路径 — server/app/api/auth.py ~line 68-71
user = User(
    username=form_data.username,
    hashed_password=hashed_password,
    is_active=False,   # ← 恢复为 False
    is_admin=False
)
```

### 注意事项

- ✅ **当前阶段**（Phase 1.2 基础设施）允许此临时改动
- ⚠️ **进入 Phase 2（好友系统）前**必须确认是否需要激活机制
- 🔔 **AGENTS.md** 已添加此提醒（见"关键非直观事实"末尾）