# AGENTS.md

## 项目概览

混合项目，包含三个组件：
- **Electron 桌面应用**: `qq-pet-macos/` - QQ 宠物游戏（怀旧服 v1.2.4）移植版，使用 Ruffle WASM
- **FastAPI 后端**: `server/` - 认证服务、数据持久化、多设备同步（HTTP API）
- **Docker 开发环境**: `docker-compose.yml` - PostgreSQL + 后端服务编排

## 架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        Electron 客户端                              │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    游戏逻辑层（保留）                     │   │
│  │  pet.js (内存状态) + global.setPetInfo()                │   │
│  └───────────────────────────┬─────────────────────────────┘   │
│                              │                                   │
│  ┌───────────────────────────▼─────────────────────────────┐   │
│  │              网络同步层（新增）                           │   │
│  │  - HTTP API Client (Axios)                               │   │
│  │  - RemoteStore (内存缓存 + 批量同步)                     │   │
│  └───────────────────────────┬─────────────────────────────┘   │
└───────────────────────────────┼──────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                        FastAPI 后端                              │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐                      │
│  │   HTTP API      │  │  认证服务       │                      │
│  │  - 用户CRUD     │  │  - JWT Token   │                      │
│  │  - 宠物CRUD     │  │  - 登录/注册    │                      │
│  │  - 背包CRUD     │  │  - 会话管理     │                      │
│  │  - 设置CRUD     │  │  - 单点登录踢出 │                      │
│  └────────┬────────┘  └────────┬────────┘                      │
│           │                     │                                │
│           └─────────────────────┼─────────────────────┐         │
│                                 ▼                      │         │
│  ┌─────────────────────────────────────────────────┐   │         │
│  │           SQLAlchemy ORM + PostgreSQL            │   │         │
│  │  - users, pet_data, pet_inventory, user_settings │   │         │
│  │  - sessions (用于单点登录踢出，客户端通过 401 检测) │  │         │
│  │  - friends (用户级好友)                           │   │         │
│  │  - pet_marriages (宠物婚姻历史)                   │   │         │
│  └─────────────────────────────────────────────────┘   │         │
└─────────────────────────────────────────────────────────────────┘
```

## 决策摘要

| 决策项 | 已确认方案 |
|--------|-----------|
| **认证方式** | 用户名密码登录，有注册功能 |
| **多设备登录** | 单点登录，新登录使旧 Token 失效（客户端通过 401 检测） |
| **设置同步** | `shortcuts`、`stopGrowth` 同步；`focus*` 本地存储 |
| **服务器地址** | 硬编码默认 `http://localhost:8000`，可通过 electron-store 修改 |
| **数据同步机制** | **HTTP PATCH + 1秒去抖批量同步**（RemoteStore 实现），WS 优先写入 + HTTP 兜底（双轨策略，稳定后移除 HTTP 分支） |
| **数据迁移** | 不需要（全新重构项目） |
| **Python CLI** | 完全移除 |
| **qq_pet_asar/** | 完全移除（存档参考目录） |

## 项目结构

```
qqpet_automation/
├── qq-pet-macos/              # Electron 桌面应用
│   ├── main.js                # 入口
│   ├── package.json
│   └── src/
│       ├── network/           # 网络层
│       ├── ini/               # 存储与宠物管理
│       └── windows/           # 窗口管理
├── server/                     # FastAPI 后端
│   ├── app/
│   │   ├── main.py            # FastAPI 入口
│   │   ├── config.py          # 配置
│   │   ├── database.py        # SQLAlchemy 引擎
│   │   ├── models/            # 数据模型
│   │   ├── schemas/           # Pydantic 模型
│   │   ├── api/               # API 路由
│   │   └── core/              # 核心模块（JWT、密码哈希）
│   ├── initdb.d/              # PostgreSQL 初始化脚本
│   ├── alembic/               # 数据库迁移
│   ├── Dockerfile
│   └── requirements.txt
├── docker-compose.yml         # 开发环境编排
├── .github/workflows/         # CI/CD 配置
├── docs/                       # 文档目录
│   └── API.md                 # API 接口文档
├── README.md
├── AGENTS.md
├── LICENSE
├── NOTICE.md
├── CONTRIBUTING.md
├── SECURITY.md
└── CHANGELOG.md
```

## 数据结构

### 数据库表

| 表名 | 说明 | 主要字段 |
|------|------|----------|
| `users` | 用户表 | `id`, `username`, `nickname` (唯一，默认=username), `email`, `hashed_password`, `is_active`, `is_admin` (占位符，未使用) |
| `pet_data` | 宠物数据表 | `id`, `user_id`, `info_*` (宠物属性), `max_*` (最大属性), `public_uid` (12位hex), `marriage_status`, `spouse_uid`, `intimacy`, `active_option`, `active_value`, `other_options`, `fishing` |
| `pet_inventory` | 背包表 | `id`, `user_id`, `items` (JSONB: food, commodity, medicine, background) |
| `user_settings` | 用户设置表 | `id`, `user_id`, `shortcuts` (JSONB), `stop_growth` |
| `sessions` | 会话表 | `id`, `user_id`, `token_jti`, `is_active`, `expires_at` |
| `friends` | 好友关系表 | `id`, `user_id`, `friend_user_id`, `status` (pending/accepted/blocked) |
| `pet_marriages` | 宠物婚姻表 | `id`, `pet_a_uid`, `pet_b_uid`, `user_a_id`, `user_b_id`, `status` (active/divorced/widowed/annulled), `intimacy` |

### 宠物数据结构

```json
{
  "info": {
    "name": "宝宝", "host": "主人", "sex": "GG",
    "growth": 0.0, "hunger": 3100, "clean": 3100,
    "health": 5, "mood": 1000, "yb": 300,
    "intel": 6, "charm": 7, "strong": 7,
    "birth_day": "", "online_time": 0.0, "last_login_time": 0,
    "online_data_time": 0.0
  },
  "max_info": {
    "level": 1, "hunger": 3100, "clean": 3100,
    "mood": 1000, "growth_rate": 260, "up_growth": 0,
    "next_growth": 100, "stop_growth": false
  },
  "active_option": {},
  "active_value": {},
  "other_options": {},
  "fishing": {}
}
```

### 背包数据结构

```json
{
  "food": ["_102010001-2", "_102010012-3"],
  "commodity": ["_102020007-1", "_102020012-2"],
  "medicine": ["_60001-2"],
  "background": []
}
```

物品编码格式：`_<物品ID>-<数量>`

### 三维（intel / charm / strong）

三维是宠物出生的基础属性，用于区分宠物风格。运作机理：

| 属性 | 字段 | 说明 |
|------|------|------|
| **智力** | `info.intel` | 通过学习（语文、数学等）、工作（律师、科研等）、物品获得 |
| **魅力** | `info.charm` | 通过学习（音乐、艺术等）、工作（演员、歌手等）、物品获得 |
| **武力** | `info.strong` | 通过学习（体育、武术等）、工作（保安、教练等）、物品获得 |

**关键规则**：
1. **出生随机分配** — 每次 `POST /api/pet/init`（含 `?reset=1`）随机生成三个 1-10 的整数，总和固定 **20**。例如 `{7,6,7}`（均衡）、`{10,5,5}`（智慧型）、`{4,6,10}`（武力型）
2. **纯奖励计数器** — 三维**不参与**任何游戏逻辑计算（增长率、等级门槛、工作要求、小游戏）。它们只通过工作/学习/物品消耗累积增长
3. **不设上限** — 三维的 `max_info` 未定义（代码中回退为 `999999999999`），可通过食物、药品、工作、学习持续增长
4. **工作准入只看等级 + 学习阶段** — 所有 18 种工作的门槛仅检查宠物等级（`need`）和各学科课时数（`education`），不检查三维值

**后端存储**: 均为 `INTEGER` 列（`info_intel`, `info_charm`, `info_strong`），作为普通数值与其他属性同等对待。

### 元宝经济体系

### 初始状态
- 出生 YB: **300**
- 减去随机新手物资价值 (15-160 YB) 后实际余额: **140-285 YB**

### 收入（工作报酬）

| 工作 | 等级 | YB/次 | 时长 | 教育要求 |
|------|------|-------|------|---------|
| 搬砖 | Lv0 | +10 | 30min | 无 |
| 泥瓦工 | Lv3 | +10 | 30min | 劳技 9 |
| 花匠 | Lv6 | +13 | 30min | 礼仪 9 |
| 木匠 | Lv6 | +13 | 30min | 劳技 9 |
| 园丁 | Lv9 | +14 | 30min | 语文 9, 艺术 9 |
| 保安 | Lv9 | +14 | 30min | 政治 9, 武术 9 |
| 演员 | Lv9 | +14 | 30min | 礼仪 9, 劳技 9 |
| 教练 | Lv12 | +16 | 30min | 武术 20 |
| 律师 | Lv12 | +16 | 30min | 政治 20 |
| 歌手 | Lv12 | +16 | 30min | 音乐 20 |
| 漫画家 | Lv15 | **+80** | 30min | 艺术 20 |
| 警察 | Lv15 | +17 | 30min | 武术 20 |
| 词曲者 | Lv15 | +17 | 30min | 音乐 20 |
| 编辑 | Lv18 | +18 | 30min | 语文 40 |
| 摄影师 | Lv18 | +18 | 30min | 艺术 40 |
| 科研人员 | Lv19 | +1024 | 80min | 数学 40 |
| 公务员 | Lv19 | +2048 | 120min | 政治 40 |

> 工作期间额外消耗饥饿/清洁，净收益低于表面数值（详见被动消耗）。

### 次要收入
- **钓鱼**: 出售渔获可得 2-140 YB/条

### 支出

| 类别 | 价格范围 | 备注 |
|------|---------|------|
| 食品 | 5-100 YB | 恢复饥饿值 |
| 清洁品 | 10-75 YB | 恢复清洁值 |
| 药品 | 50-400 YB | 恢复健康值 |
| 学习课时 | 按科目等级定价 | 消耗型支出 |
| 工作激活 | 20 YB/次 | 每次工作前扣除 |

### 被动消耗（影响净收益）

| 状态 | 饥饿/min | 清洁/min | 心情/min |
|------|---------|---------|---------|
| 空闲 | rand(5,8) | rand(5,8) | rand(2,4) |
| 工作中 | +额外 starve/useTime | +额外 clean/useTime | +额外 mood/useTime |
| 学习中 | rand(5,8)+2 | rand(5,8)+1 | rand(2,4) |

### 关键规则
- 三维不影响 YB 经济
- 工作准入仅检查**等级 + 教育课时**，不检查三维
- 300 YB 出生资金确保不搬砖也能撑到 Lv6（花匠开始自给自足）
- Lv15（漫画家）之前所有工作均为净亏损或微利

### 设置数据结构

```json
{
  "shortcuts": {},
  "stop_growth": false
}
```

**同步字段**：`shortcuts`, `stop_growth`  
**本地字段**：`focusEnabled`, `doNotDisturb`

## API 端点索引

### 认证 API (`/api/auth`)

| 方法 | 端点 | 描述 | 认证 |
|------|------|------|------|
| POST | `/api/auth/register` | 用户注册 | 否 |
| POST | `/api/auth/login` | 登录获取 Token | 否 |
| POST | `/api/auth/logout` | 登出（使 Token 失效） | 是 |
| GET | `/api/auth/me` | 获取当前用户信息 | 是 |
| POST | `/api/auth/refresh` | 刷新 Token | 是 |

### 宠物数据 API (`/api/pet`)

| 方法 | 端点 | 描述 | 认证 |
|------|------|------|------|
| GET | `/api/pet` | 获取完整宠物数据 | 是 |
| PATCH | `/api/pet` | 增量更新宠物数据 | 是 |
| GET | `/api/pet/info` | 获取宠物属性 | 是 |
| PATCH | `/api/pet/info` | 增量更新宠物属性 | 是 |
| GET | `/api/pet/active-option` | 获取活动状态 | 是 |
| PATCH | `/api/pet/active-option` | 更新活动状态 | 是 |

### 背包 API (`/api/pet/inventory`)

| 方法 | 端点 | 描述 | 认证 |
|------|------|------|------|
| GET | `/api/pet/inventory` | 获取背包 | 是 |
| PATCH | `/api/pet/inventory` | 更新背包 | 是 |
| POST | `/api/pet/inventory/use` | 使用物品 | 是 |

### 设置 API (`/api/pet/settings`)

| 方法 | 端点 | 描述 | 认证 |
|------|------|------|------|
| GET | `/api/pet/settings` | 获取同步设置 | 是 |
| PATCH | `/api/pet/settings` | 更新同步设置 | 是 |

## 开发命令

### Electron 应用
```bash
cd qq-pet-macos
npm install
npx electron .          # 本地运行
npm run build           # 构建 macOS dmg + zip
npm run build:win       # 构建 Windows
npm run build:linux     # 构建 Linux
```

### 后端服务（开发环境）
```bash
# 使用 Docker（推荐，含 PostgreSQL）
docker-compose up -d postgres
cd server
source .venv/bin/activate
uvicorn app.main:app --reload

# 或使用 SQLite（单机开发）
cd server
source .venv/bin/activate
uvicorn app.main:app --reload
```

### 数据库迁移
```bash
cd server
alembic revision --autogenerate -m "描述"
alembic upgrade head
```

### 后端测试
```bash
cd server
pytest
```

## 关键非直观事实

- **Electron 版本锁定 v28** - Electron 33 导致回归问题（在 v1.6.1 中已回退），请使用 v28 + electron-builder v24
- **无代码检查/类型检查** - 不存在 eslint、ruff、mypy 或 prettier 配置。只有 pytest 用于测试。
- **数据同步机制** - HTTP PATCH + 1秒去抖批量同步（RemoteStore 实现），WS 优先写入 + HTTP 兜底（双轨策略，稳定后移除 HTTP 分支）
- **单点登录踢出** - 新登录使旧会话 `is_active=false`，客户端通过 HTTP 401 检测并刷新 Token，刷新失败则显示登录窗口
- **存储方案** - 运行时依赖内存（RemoteStore.cache），不再使用 `fs.watch` 监听本地文件
- **CI 触发条件** - 仅在 `v*` 标签或 `workflow_dispatch` 时构建
- **macOS 未签名应用** - 需要执行：`sudo xattr -rd com.apple.quarantine /Applications/QQ宠物.app`
- **面向用户的语言** - 所有 README 和文档均使用**中文**
- **服务器地址配置** - 硬编码默认 `http://localhost:8000`，可通过 electron-store 修改
- **SQLAlchemy JSON 列必须新建 dict 赋值** - SQLAlchemy 2.0 `JSON` 列不支持原地修改检测（`items[key]=v`）。必须用 `dict(existing)` 创建副本再赋值：`new = dict(obj.json_col or {}); new[k]=v; obj.json_col = new`
- **register 已改 is_active=True** - 原代码注册用户标记为 `is_active=False` 需管理员激活。为方便开发已移除该限制，新注册用户自动激活
- **右键菜单动态替换改为 value 标识** - 原 `changeMenu` 消息使用硬编码数组索引（如 `[4]`、`[3,0]`），添加菜单项后索引偏移导致替换错位。已重构为按 `targetValue`（菜单项的 `value` 字段）搜索替换，`l(targetValue, newItem)` 替代 `l(newItem, positionArray)`，新增菜单不再需要同步更新索引

## 代码规范

- **提交信息**: 约定式提交风格：`feat(cli):`、`fix(sync):`、`docs(readme):`
- **Python**: 必须使用类型注解，路径使用 `pathlib.Path`，不允许原地修改
- **JavaScript**: 使用 `const`/`let`（禁用 `var`），使用 `async/await`
- **分支命名**: `feat/xxx`、`fix/xxx`、`docs/xxx`

## 相关文件

- `.github/workflows/build.yml` - CI/CD 在 `v*` 标签时构建 macOS/Windows/Linux 版本 + 后端测试
- `server/app/main.py` - FastAPI 入口
- `server/app/models/` - SQLAlchemy 数据模型（含 PetData、Friend、PetMarriage）
- `server/app/api/` - API 路由
- `server/initdb.d/` - PostgreSQL 初始化脚本（开发环境）
- `docs/API.md` - 完整 API 接口文档
- `qq-pet-macos/src/ini/remoteStore.js` - 客户端远程存储同步
- `qq-pet-macos/src/network/` - 客户端网络层（api.js, auth.js, login 窗口）
