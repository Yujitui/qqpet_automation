# QQ 宠物服务器-客户端架构重构计划

> 文档版本：v1.5  
> 最后更新：2026年5月11日  
> 状态：**重构完成** ✅  
> 更新记录：
> - v1.0: 初始版本
> - v1.1: 新增阶段 0 在线资源备份；更新数据库初始化方案（initdb.d + Alembic）；更新快速恢复指南
> - v1.2: **阶段一完成**；添加 SQLite 本地开发支持；添加注册端点（原计划"无注册功能"已调整）；添加 WebSocket 即时踢出
> - v1.3: **阶段二完成**；移除客户端 WebSocket（改用 HTTP 批量同步）；移除 dataWatcher（运行时依赖内存）；简化被踢出检测（HTTP 401 机制）
> - v1.4: **清理后端 WebSocket**；客户端+后端均移除 WebSocket（完全移除，不再作为备选方案）
> - v1.5: **阶段三完成**；删除旧代码、更新所有文档、配置 CI/CD；**重构全部完成**

---

## 一、项目概述

### 1.1 当前架构

```
┌─────────────────────────────────────────────────────────────┐
│                    当前本地架构                                │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Electron 主进程                          │   │
│  │  ┌──────────┐  ┌──────────────┐  ┌──────────────┐ │   │
│  │  │ pet.js   │  │ $Store       │  │dataWatcher.js│ │   │
│  │  │(内存状态) │◀▶│(electron-   │◀▶│(fs.watch监   │ │   │
│  │  │          │  │ store)       │  │ 听本地文件)   │ │   │
│  │  └────┬─────┘  └──────┬───────┘  └──────────────┘ │   │
│  │       │                │                              │   │
│  │       ▼                ▼                              │   │
│  │  ┌──────────────────────────────────────────────┐   │   │
│  │  │     config-macos.json (本地 JSON 文件)        │   │   │
│  │  └──────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 目标架构

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
│  │  - 替换 $Store / 移除 dataWatcher.js                     │   │
│  └───────────────────────────┬─────────────────────────────┘   │
└──────────────────────────────┼──────────────────────────────────┘
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
│  └─────────────────────────────────────────────────┘   │         │
└─────────────────────────────────────────────────────────────────┘
```

---

## 二、决策摘要

| 决策项 | 已确认方案 |
|--------|-----------|
| **认证方式** | 用户名密码登录，**有注册功能**（开发阶段便捷测试，生产环境可考虑禁用） |
| **多设备登录** | 单点登录，新登录使旧 Token 失效（客户端通过 401 检测） |
| **设置同步** | `shortcuts`、`stopGrowth` 同步；`llm*`、`focus*` 本地存储 |
| **服务器地址** | 硬编码默认 `http://localhost:8000`，可通过 electron-store 修改 |
| **数据同步机制** | **HTTP PATCH + 1秒去抖批量同步**（RemoteStore 实现） |
| **数据迁移** | 不需要（全新重构项目） |
| **Python CLI** | 完全移除 |
| **qq_pet_asar/** | 完全移除（存档参考目录） |

---

## 三、项目结构

```
qqpet_automation/
├── qq-pet-macos/              # Electron 客户端（改造）
│   ├── main.js                 # 入口
│   ├── package.json
│   ├── src/
│   │   ├── network/            # 【新增】网络层
│   │   │   ├── api.js          # Axios 封装 + 自动刷新 Token
│   │   │   ├── auth.js         # 登录/Token 管理
│   │   │   └── login/          # 登录窗口
│   │   ├── ini/
│   │   │   ├── remoteStore.js  # 【新增】远程存储实现（HTTP 批量同步）
│   │   │   ├── dataWatcher.js  # 【已删除】不再需要（运行时依赖内存）
│   │   │   └── ...
│   │   ├── windows/
│   │   │   ├── popups/
│   │   │   │   └── login/      # 【新增】登录窗口
│   │   │   │       ├── index.html
│   │   │   │       ├── index.js
│   │   │   │       └── preload.js
│   │   │   └── ...
│   │   └── ...
│   └── resources/
│
├── server/                      # 【新增】FastAPI 后端
│   ├── app/
│   │   ├── main.py              # FastAPI 入口
│   │   ├── config.py            # 配置（环境变量读取）
│   │   ├── database.py          # SQLAlchemy 引擎/Session
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── user.py          # 用户模型
│   │   │   ├── pet.py           # 宠物数据模型
│   │   │   ├── inventory.py     # 背包模型
│   │   │   ├── settings.py      # 设置模型
│   │   │   └── session.py       # 会话/在线状态
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── user.py          # Pydantic 用户模型
│   │   │   ├── pet.py           # Pydantic 宠物模型
│   │   │   ├── inventory.py     # Pydantic 背包模型
│   │   │   ├── settings.py      # Pydantic 设置模型
│   │   │   └── auth.py          # 认证相关 schema
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── deps.py          # 依赖注入
│   │   │   ├── auth.py          # 登录 API
│   │   │   ├── pet.py           # 宠物 CRUD
│   │   │   ├── inventory.py     # 背包 CRUD
│   │   │   └── settings.py      # 设置 CRUD
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   └── security.py      # JWT、密码哈希
│   │   └── requirements.txt
│   ├── initdb.d/                 # 【新增】PostgreSQL 初始化脚本（开发环境）
│   │   ├── 001_init_schema.sql  # 表结构初始化
│   │   └── 002_seed_data.sql    # 种子数据
│   ├── alembic/                 # 数据库迁移（生产环境版本管理）
│   ├── alembic.ini
│   ├── .env.example             # 环境变量示例
│   └── Dockerfile               # 容器化
│
├── docker-compose.yml           # 【新增】开发环境编排
│
├── .github/
│   └── workflows/
│       └── build.yml            # 【改造】增加后端 CI
│
├── REFACTOR_PLAN.md             # 本文档
├── AGENTS.md                    # 【改造】更新
├── README.md                    # 【改造】更新
├── NOTICE.md                    # 【改造】更新（移除 qq_pet_asar 引用）
│
├── src/                         # 【删除】Python CLI
├── tests/                       # 【删除】
├── config.yaml                  # 【删除】
├── pyproject.toml               # 【删除】
├── requirements.txt             # 【删除】
├── skills/                      # 【删除】
└── qq_pet_asar/                 # 【删除】存档参考目录
```

---

## 四、实施阶段

### 阶段 0：在线资源备份（风险缓解）

**注意**：此阶段为可选的风险缓解步骤，用于防止外部资源不可用。

#### 0.1 现有资源依赖分析

| 资源 | 来源 | 稳定性风险 | 当前状态 |
|------|------|-------------|----------|
| `qq-pet-resources.tar.gz` | GitHub Release (`resources-v1` 标签) | **中高** | CI 构建时下载 |
| npm 依赖 | npm registry | **低** | 本地有 package.json |
| Python 依赖 | PyPI | **低** | 本地有 requirements.txt |

#### 0.2 关键发现

**Git 已跟踪的资源**：
- `qq-pet-macos/src/assets/` 有 **3416 个文件** 被 git 跟踪
- 包括 `.swf` 动画、图片、字体等

**CI 额外下载的资源**：
```bash
# .github/workflows/build.yml 中的步骤：
gh release download resources-v1 \
  --pattern 'qq-pet-resources.tar.gz'
```

**需要确认的问题**：
1. `qq-pet-resources.tar.gz` 包含什么？
2. 是否与 git 跟踪的 `src/assets/` 内容重复？
3. 是否有 Git LFS 占位符文件？

#### 0.3 建议的备份措施

**任务清单**：
- [ ] 检查是否有 Git LFS 文件：`git lfs ls-files`
- [ ] 下载 `qq-pet-resources.tar.gz` 并分析内容
- [ ] 确认与 git 跟踪内容的差异
- [ ] 如果有补充文件，添加到 git 跟踪或创建独立资源备份

**备份方案**：

如果确认 `qq-pet-resources.tar.gz` 包含 git 未跟踪的内容：

```bash
# 方案 A：添加到 git 跟踪（文件不大时）
# 解压后对比，添加缺失的文件

# 方案 B：创建独立资源标签
# 创建 resources-v2 标签，上传完整资源包
```

**CI 备选方案**：

如果 GitHub Release 资源不可用，可以考虑：
1. 将所有必要资源纳入 git 跟踪
2. 或使用 Git LFS 管理大文件
3. 或使用第三方对象存储（如 S3）作为备选

---

### 阶段一：后端基础设施

#### 1.1 初始化后端项目

**任务清单**：
- [ ] 创建 `server/` 目录结构
- [ ] 创建 `requirements.txt` 依赖文件
- [ ] 创建 `app/main.py` FastAPI 入口
- [ ] 创建 `app/config.py` 配置模块（读取环境变量）
- [ ] 创建 `app/database.py` SQLAlchemy 引擎和 Session

**依赖清单**：
```txt
fastapi>=0.109.0
uvicorn[standard]>=0.27.0
sqlalchemy>=2.0.0
alembic>=1.13.0
psycopg2-binary>=2.9.9
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4
python-multipart>=0.0.6
pydantic>=2.5.0
pydantic-settings>=2.1.0
```

**环境变量**（`.env.example`）：
```env
# 数据库配置
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/qqpet

# JWT 配置
JWT_SECRET_KEY=your-secret-key-change-me-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# 服务器配置
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
```

#### 1.2 数据库模型设计

**表结构**：

```sql
-- 用户表
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP
);

-- 宠物数据表
CREATE TABLE pet_data (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- pet.info (独立字段方便查询)
    info_name VARCHAR(50) DEFAULT '',
    info_host VARCHAR(50) DEFAULT '',
    info_sex VARCHAR(2) DEFAULT 'GG',
    info_growth FLOAT DEFAULT 0,
    info_hunger INTEGER DEFAULT 3100,
    info_clean INTEGER DEFAULT 3100,
    info_health INTEGER DEFAULT 5,
    info_mood INTEGER DEFAULT 1000,
    info_yb INTEGER DEFAULT 300,
    info_intel INTEGER DEFAULT 100,
    info_charm INTEGER DEFAULT 215,
    info_strong INTEGER DEFAULT 123,
    info_birth_day VARCHAR(20) DEFAULT '',
    info_online_time FLOAT DEFAULT 0,
    info_last_login_time INTEGER DEFAULT 0,
    info_online_data_time FLOAT DEFAULT 0,
    
    -- pet.maxInfo
    max_level INTEGER DEFAULT 1,
    max_hunger INTEGER DEFAULT 3100,
    max_clean INTEGER DEFAULT 3100,
    max_mood INTEGER DEFAULT 1000,
    max_growth_rate INTEGER DEFAULT 260,
    max_up_growth INTEGER DEFAULT 0,
    max_next_growth INTEGER DEFAULT 100,
    max_stop_growth BOOLEAN DEFAULT FALSE,
    
    -- 复杂结构用 JSONB
    active_option JSONB DEFAULT '{}',
    active_value JSONB DEFAULT '{}',
    other_options JSONB DEFAULT '{}',
    fishing JSONB DEFAULT '{}',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 背包表
CREATE TABLE pet_inventory (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    items JSONB DEFAULT '{"food": [], "commodity": [], "medicine": [], "background": []}'
);

-- 用户设置表（同步部分）
CREATE TABLE user_settings (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    shortcuts JSONB DEFAULT '{}',
    stop_growth BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 会话表（用于单点登录踢出）
CREATE TABLE sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_jti VARCHAR(100) UNIQUE NOT NULL,
    device_info JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL
);
```

**SQLAlchemy 模型文件**：
- `app/models/user.py` - `users` 表
- `app/models/pet.py` - `pet_data` 表
- `app/models/inventory.py` - `pet_inventory` 表
- `app/models/settings.py` - `user_settings` 表
- `app/models/session.py` - `sessions` 表

#### 1.3 数据库初始化方案

**两种方案对比**：

| 方案 | 适用场景 | 说明 |
|------|---------|------|
| **A. docker-entrypoint-initdb.d** | 开发环境快速启动 | PostgreSQL 容器启动时自动执行初始化脚本 |
| **B. Alembic 迁移** | 生产环境、版本管理 | 支持 schema 升级/回滚，用于后续变更 |

**推荐方案：两者结合**

```
开发环境：initdb.d 快速初始化
生产环境：Alembic 管理版本迁移
```

---

**方案 A：docker-entrypoint-initdb.d（开发环境快速启动）**

将 SQL 初始化脚本放入 `server/initdb.d/` 目录：

```
server/
├── initdb.d/
│   └── 001_init_schema.sql    # 表结构初始化
│   └── 002_seed_data.sql      # 种子数据（可选管理员用户）
```

**docker-compose.yml 配置**：
```yaml
services:
  postgres:
    image: postgres:16-alpine
    volumes:
      - ./server/initdb.d:/docker-entrypoint-initdb.d
      - postgres_data:/var/lib/postgresql/data
```

> 注意：`docker-entrypoint-initdb.d/` 仅在容器首次启动时执行（当数据卷为空时）。

---

**方案 B：Alembic 迁移（版本管理）**

**任务清单**：
- [ ] 初始化 alembic：`alembic init alembic`
- [ ] 配置 `alembic.ini` 和 `alembic/env.py`
- [ ] 创建初始迁移：`alembic revision --autogenerate -m "initial"`
- [ ] 应用迁移：`alembic upgrade head`

**适用场景**：
- 生产环境部署
- 后续 schema 变更（添加新字段、新表等）
- 需要回滚能力的场景

#### 1.4 认证核心实现

**文件**：`app/core/security.py`

**功能**：
- [ ] 密码哈希（bcrypt）
- [ ] 密码验证
- [ ] JWT Token 创建（access_token + refresh_token）
- [ ] JWT Token 验证
- [ ] JTI（Token ID）生成（用于会话管理）

#### 1.5 认证 API 实现

**文件**：`app/api/auth.py`

**端点**：

| 方法 | 端点 | 描述 | 认证 |
|------|------|------|------|
| POST | `/api/auth/login` | 登录获取 Token | 否 |
| POST | `/api/auth/logout` | 登出（使 Token 失效） | 是 |
| GET | `/api/auth/me` | 获取当前用户信息 | 是 |
| POST | `/api/auth/refresh` | 刷新 Token | 是 |

**请求/响应格式**：

**登录请求**：
```json
POST /api/auth/login
{
  "username": "xxx",
  "password": "xxx"
}
```

**登录响应**：
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "id": 1,
    "username": "xxx",
    "is_admin": false
  }
}
```

#### 1.6 宠物数据 CRUD API

**文件**：`app/api/pet.py`

**端点**：

| 方法 | 端点 | 描述 |
|------|------|------|
| GET | `/api/pet` | 获取完整宠物数据 |
| PATCH | `/api/pet` | 增量更新宠物数据 |
| GET | `/api/pet/info` | 获取 pet.info |
| PATCH | `/api/pet/info` | 增量更新 pet.info |
| GET | `/api/pet/active-option` | 获取活动状态 |
| PATCH | `/api/pet/active-option` | 更新活动状态 |

**增量更新请求示例**：
```json
PATCH /api/pet
{
  "info": {
    "hunger": 2500,
    "clean": 2800
  },
  "active_option": {
    "ill": null
  }
}
```

#### 1.7 背包/设置 API

**文件**：
- `app/api/inventory.py` - 背包 API
- `app/api/settings.py` - 设置 API

**背包端点**：

| 方法 | 端点 | 描述 |
|------|------|------|
| GET | `/api/pet/inventory` | 获取背包 |
| PATCH | `/api/pet/inventory` | 更新背包 |
| POST | `/api/pet/inventory/use` | 使用物品 |

**设置端点**：

| 方法 | 端点 | 描述 |
|------|------|------|
| GET | `/api/pet/settings` | 获取同步设置 |
| PATCH | `/api/pet/settings` | 更新同步设置 |

#### 1.8 WebSocket 实现（已移除）

**设计变更**：
- **原计划**：WebSocket 实时同步（数据广播）+ 实时踢出
- **实际实现**：v1.4 完全移除 WebSocket（客户端 + 后端）

**删除的文件/代码**：
- `app/core/websocket.py` - WebSocket 连接管理
- `app/main.py` - WebSocket 路由 `/ws/sync`
- `app/api/auth.py` - `manager.kick_user()` 调用

#### 1.9 单点登录踢出逻辑

**实现要点**：
1. 登录时创建 `sessions` 记录，生成唯一 `token_jti`
2. JWT Token payload 包含 `jti` 字段
3. 验证 Token 时检查 `sessions.is_active`
4. 新登录时将该用户所有旧会话 `is_active` 设为 `false`
5. **客户端检测**：后续请求收到 401 时尝试刷新 token，刷新失败则显示登录窗口

**说明**：
- 原计划：WebSocket 实时接收 `kicked` 消息
- 实际实现：通过 HTTP 401 机制实现（简化版，无需 WebSocket）
- 效果：新设备登录后，旧设备下次请求时会被强制回到登录界面

#### 1.10 阶段一检查点

**完成后验证**：
- [x] 数据库迁移成功
- [x] 可以通过 API 登录/登出
- [x] 可以获取/更新宠物数据
- [x] 新登录会使旧会话失效（`is_active = false`）
- [x] 简化版踢出：旧设备请求收到 401 → 显示登录窗口

---

### 阶段二：Electron 客户端改造

#### 2.1 新增网络层

**文件结构**：
```
qq-pet-macos/src/network/
├── auth.js         # Token 管理
├── api.js          # Axios 封装
├── websocket.js    # WebSocket 连接管理
└── sync.js         # 同步逻辑
```

#### 2.2 auth.js - Token 管理

**功能**：
- [ ] `getAccessToken()` - 获取访问 Token
- [ ] `getRefreshToken()` - 获取刷新 Token
- [ ] `setTokens()` - 保存 Token
- [ ] `clearTokens()` - 清除 Token
- [ ] `isAuthenticated()` - 检查是否已登录
- [ ] 本地存储使用 `electron-store`（仅存敏感配置）

#### 2.3 api.js - Axios 封装

**功能**：
- [ ] 读取服务器地址（默认 `http://localhost:8000`）
- [ ] 请求拦截器：自动注入 `Authorization: Bearer <token>`
- [ ] 响应拦截器：401 时自动刷新 Token
- [ ] 刷新失败时跳转登录界面

#### 2.4 websocket.js - WebSocket 管理（已移除）

**设计决策变更**：
- **原计划**：使用 WebSocket 进行实时数据同步和多设备踢出
- **实际实现**：已移除。改用 HTTP 批量同步（RemoteStore）和 401 检测实现踢出

**替代方案**：
- **数据同步**：RemoteStore 使用 HTTP PATCH + 1秒去抖批量同步
- **单点登录踢出**：服务器端将旧会话标记为 `is_active=false`，客户端后续请求收到 401 时尝试刷新 token，刷新失败则显示登录窗口（`global.onAuthRequired`）

#### 2.5 RemoteStore 实现

**文件**：`qq-pet-macos/src/ini/remoteStore.js`

**核心逻辑**：
- [ ] 内存缓存减少网络请求
- [ ] `getItem(key)` - 根据 key 从不同来源获取
  - `pet` → API `/api/pet`
  - `cache` → API `/api/pet/inventory`
  - `sys` → 混合（同步部分 + 本地部分）
- [ ] `setItem(key, value)` - 同步到服务器
- [ ] 设置分离：同步字段（shortcuts, stopGrowth）vs 本地字段（llmConfig, focusConfig）

#### 2.6 替换 $Store

**修改文件**：`qq-pet-macos/src/ini/store.js` 或 `init.js`

**操作**：
- [ ] 将 `global.$Store = new St()` 替换为 `global.$Store = new RemoteStore()`

#### 2.7 移除 dataWatcher

**删除文件**：
- [x] `qq-pet-macos/src/ini/dataWatcher.js`

**修改文件**：
- [x] `qq-pet-macos/main.js` - 移除 `startDataWatcher()` 调用

**说明**：
- 原计划：不再需要 `fs.watch` 监听本地文件，数据变更来自 WebSocket 推送
- 实际实现：运行时完全依赖内存状态。数据从服务器加载后存储在 `RemoteStore.cache` 中，`$Store.getItem()`/`setItem()` 直接操作内存。同步通过 HTTP PATCH 批量进行。

#### 2.8 新增登录窗口

**文件**：
```
qq-pet-macos/src/windows/popups/login/
├── index.html    # 登录界面 HTML
├── index.js      # 登录逻辑（Vue + Ant Design）
└── preload.js    # IPC 桥接
```

**功能**：
- [ ] 用户名输入
- [ ] 密码输入
- [ ] 服务器地址配置（可选，默认 localhost:8000）
- [ ] 登录按钮
- [ ] 错误提示
- [ ] 登录成功后保存 Token，关闭登录窗口，显示主窗口

#### 2.9 改造启动流程

**修改文件**：`qq-pet-macos/main.js`

**新流程**：
```
1. app.whenReady()
   ↓
2. 检查 isAuthenticated()
   ├── 是 → 验证 Token 有效性（调用 GET /api/auth/me）
   │           ├── 有效 → RemoteStore.init() → loadGame()
   │           └── 无效 → clearTokens() → showLoginWindow()
   └── 否 → showLoginWindow()
```

**实际实现**：
- 启动时检查 Token 有效性
- 有效时调用 `RemoteStore.init()` 从服务器加载数据
- 失效或过期时显示登录窗口

#### 2.10 被踢出处理逻辑

**触发条件**：HTTP 401 响应（Token 已失效，因新登录被踢出）

**服务器端实现**：
- 新设备登录时，将该用户所有旧会话标记为 `sessions.is_active = false`
- 后续请求携带旧 Token 时，`get_current_user()` 检测到会话已失效，返回 401

**客户端处理流程**（`api.js` 响应拦截器）：
```
1. 请求收到 401 响应
   ↓
2. 尝试用 refresh_token 刷新 Token
   ├── 成功 → 更新 Token，重试原请求
   └── 失败（refresh_token 也被标记失效）
           ↓
3. auth.clearTokens() 清除本地 Token
   ↓
4. global.onAuthRequired() 显示登录窗口
```

**说明**：
- 原计划：通过 WebSocket 实时接收 `kicked` 消息
- 实际实现：通过 HTTP 401 机制实现（简化版，无需 WebSocket）
- 效果：新设备登录后，旧设备下次请求时会被强制回到登录界面

#### 2.11 阶段二检查点

**完成后验证**：
- [x] 启动后显示登录界面
- [x] 可以用有效账号登录
- [x] 登录后显示主游戏窗口
- [x] 游戏数据从服务器加载
- [x] 游戏操作（喂食、洗澡）会同步到服务器（HTTP PATCH 批量同步）
- [x] 简化版踢出：新登录会使旧 Token 失效，旧设备下次请求时 401 → 显示登录窗口

---

### 阶段三：清理与文档

#### 3.1 删除旧代码

**删除目录/文件**：
- [x] `src/` - Python CLI 源码
- [x] `tests/` - Python 测试
- [x] `skills/` - OpenClaw 技能
- [x] `qq_pet_asar/` - 原始版本存档（资源已在 `qq-pet-macos/` 中重复）
- [x] `config.yaml` - Python CLI 配置
- [x] `pyproject.toml` - Python 项目配置
- [x] `requirements.txt` - Python 依赖

**删除统计**：
- `src/`: 8 个文件
- `tests/`: 3 个文件
- `skills/`: 1 个文件（含硬编码路径）
- `qq_pet_asar/`: ~3676 个文件

#### 3.2 创建 Docker 开发环境

**状态**：✅ 已就绪（在阶段一创建）

**已存在的文件**：
- `docker-compose.yml` - 包含 postgres + backend + adminer 三个服务
- `server/Dockerfile` - 基于 python:3.11-slim
- `server/initdb.d/*.sql` - 数据库初始化脚本

**使用方式**：
```bash
docker-compose up -d postgres
cd server
source .venv/bin/activate
uvicorn app.main:app --reload
```

#### 3.3 更新文档

**更新的文件**：
- [x] `README.md` - 更新项目介绍、架构图、开发指南
  - 移除 Python CLI 和 OpenClaw Skill 相关内容
  - 新增 FastAPI 后端服务架构描述
  - 新增 Docker 开发环境启动指南
  - 更新项目结构图

- [x] `AGENTS.md` - 更新架构信息、开发命令
  - 移除 Python CLI 相关内容
  - 新增 FastAPI 后端服务描述
  - 新增 Docker、uvicorn、alembic 开发命令
  - 更新关键非直观事实

- [x] `NOTICE.md` - 移除对 `qq_pet_asar/`、`qq_pet_app/` 的引用
  - 移除 Python CLI 原创部分描述
  - 新增 FastAPI 后端原创部分描述

- [x] `CONTRIBUTING.md` - 更新贡献指南
  - 移除 Python CLI 相关贡献指引
  - 新增后端服务开发指南

- [x] `SECURITY.md` - 更新安全策略
  - 移除 Python CLI 相关描述
  - 新增后端 API 安全相关描述

- [x] `CHANGELOG.md` - 归档旧历史
  - 顶部添加重构后版本策略（v2.0.0 开始）
  - 添加 v2.0.0 (Unreleased) 变更记录
  - 将 v1.2.4-clean ~ v1.6.0 移到"历史归档"部分

#### 3.4 更新 CI/CD

**修改的文件**：`.github/workflows/build.yml`

**新增内容**：
- [x] 新增 `test-backend` job
  - Python 3.11 环境搭建
  - 后端依赖安装
  - 后端导入测试（models、API、main）
  - 基本端点测试（`/health`、`/`）

**依赖更新**：
- [x] `server/requirements.txt` - 移除 `websockets>=12.0`，添加 `pytest>=7.0.0`

#### 3.5 阶段三检查点

**完成后验证**：
- [x] 旧代码已从 git 中移除
- [x] Docker 环境可以正常启动 PostgreSQL
- [x] 文档已更新（无 Python CLI 引用）
- [x] 后端导入测试通过
- [x] CI 工作流新增后端测试 job

---

## 五、数据结构参考

### 5.1 宠物数据完整结构

```json
{
  "info": {
    "name": "我",
    "host": "主",
    "sex": "GG",
    "growth": 0,
    "hunger": 3100,
    "clean": 3100,
    "health": 5,
    "mood": 1000,
    "yb": 300,
    "intel": 100,
    "charm": 215,
    "strong": 123,
    "birthDay": "26-05-09 10",
    "onLineTime": 0,
    "lastLoginTime": 0,
    "onlineDataTime": 0
  },
  "maxInfo": {
    "stopGrowth": false,
    "level": 1,
    "upGrowth": 0,
    "nextGrowth": 100,
    "growthRate": 260,
    "hunger": 3100,
    "clean": 3100,
    "health": 5,
    "mood": 1000
  },
  "activeValue": {
    "work": {},
    "study": {
      "chinese": 0,
      "mathematics": 0,
      "politics": 0,
      "music": 0,
      "art": 0,
      "manner": 0,
      "pe": 0,
      "labouring": 0,
      "wushu": 0
    }
  },
  "activeOption": {
    "work": null,
    "study": null,
    "trip": null,
    "ill": null,
    "die": null
  },
  "otherOptions": {
    "pinkDiamond": false,
    "growth": 0,
    "growthValue": 0,
    "growthValue_next": 0,
    "pinkDiamondLevel": 0,
    "pinkDiamondBeginDate": 0,
    "pinkDiamondExpirationDate": 0,
    "sweetHeart": false
  },
  "fishing": {
    "fishes": [],
    "harvestfish": 0,
    "allvipcnt": 0,
    "canusecnt": 0,
    "power": 30,
    "needTime": 1
  }
}
```

### 5.2 背包数据结构

```json
{
  "food": ["_102010001-2", "_102010012-3"],
  "commodity": ["_102020007-1", "_102020012-2", "_10021005-2"],
  "medicine": ["_60001-2"],
  "background": []
}
```

**物品编码格式**：`_<物品ID>-<数量>`

### 5.3 系统设置结构

```json
{
  "shortcuts": {},
  "stopGrowth": false,
  "llmEnabled": false,
  "llmApiKey": "",
  "llmModel": "",
  "focusEnabled": false,
  "doNotDisturb": false
}
```

**同步字段**：`shortcuts`, `stopGrowth`  
**本地字段**：`llmEnabled`, `llmApiKey`, `llmModel`, `focusEnabled`, `doNotDisturb`

---

## 六、风险与注意事项

### 6.1 数据一致性

- **问题**：`pet.js` 中的内存对象是真实状态源，网络延迟可能导致状态不一致
- **缓解**：关键操作（如治病）等待服务器确认后再更新 UI；高频属性（饥饿/清洁/心情）批量更新

### 6.2 离线场景

- **问题**：当前设计假设网络始终可用
- **缓解**：暂不考虑离线场景；如果后续需要，实现本地缓存 + 同步队列

### 6.3 现有代码复杂度

- **问题**：很多 JS 文件是 webpack 打包后的（一行巨长代码），可读性差
- **缓解**：优先修改清晰的源文件，打包后的文件谨慎修改

### 6.4 性能优化

- **问题**：宠物属性每秒变化，频繁 API 调用性能差
- **缓解**：
  - 本地内存状态优先，异步同步到服务器
  - 增量更新（PATCH）而非全量替换
  - 批量更新（每 5 秒一次）+ 关键操作立即同步

---

## 七、实施进度追踪

### 阶段 0：在线资源备份

| 任务 | 状态 | 完成日期 |
|------|------|----------|
| 0.1 检查 Git LFS 文件 | 待开始 | - |
| 0.2 下载并分析 qq-pet-resources.tar.gz | 待开始 | - |
| 0.3 确认与 git 跟踪内容的差异 | 待开始 | - |
| 0.4 备份或整合补充资源 | 待开始 | - |

### 阶段一：后端基础设施 ✅ **已完成**

| 任务 | 状态 | 完成日期 | 备注 |
|------|------|----------|------|
| 1.1 初始化后端项目 | ✅ 完成 | 2026-05-09 | server/ 目录结构 |
| 1.2 数据库模型设计 | ✅ 完成 | 2026-05-09 | 5 个模型文件 |
| 1.3 数据库初始化方案 | ✅ 完成 | 2026-05-09 | initdb.d + Alembic + SQLite 支持 |
| 1.4 认证核心实现 | ✅ 完成 | 2026-05-09 | bcrypt + JWT |
| 1.5 认证 API 实现 | ✅ 完成 | 2026-05-09 | login/logout/me/refresh + **新增 register** |
| 1.6 宠物数据 CRUD API | ✅ 完成 | 2026-05-09 | GET/PATCH /api/pet, /api/pet/info 等 |
| 1.7 背包/设置 API | ✅ 完成 | 2026-05-09 | /api/pet/inventory, /api/pet/settings |
| 1.8 WebSocket 实现 | ❌ 已移除 | 2026-05-11 | **设计变更**：客户端+后端均移除，完全使用 HTTP |
| 1.9 单点登录踢出逻辑 | ✅ 完成 | 2026-05-11 | 数据库 `is_active=false` + 客户端 HTTP 401 检测 |
| 1.10 阶段一检查点 | ✅ 完成 | 2026-05-09 | Docker 环境 API 测试 7/7 通过 |

### 阶段二：Electron 客户端改造

| 任务 | 状态 | 完成日期 | 备注 |
|------|------|----------|------|
| 2.1 新增网络层 | ✅ 完成 | 2026-05-09 | src/network/ 目录 |
| 2.2 auth.js - Token 管理 | ✅ 完成 | 2026-05-09 | 本地存储 + 服务器地址配置 |
| 2.3 api.js - Axios 封装 | ✅ 完成 | 2026-05-09 | 自动刷新 Token |
| 2.4 websocket.js - WebSocket 管理 | ❌ 已移除 | 2026-05-11 | **设计变更**：改用 HTTP 批量同步 + 401 检测踢出 |
| 2.5 RemoteStore 实现 | ✅ 完成 | 2026-05-09 | src/ini/remoteStore.js |
| 2.6 替换 $Store | ✅ 完成 | 2026-05-09 | main.js 中替换 |
| 2.7 移除 dataWatcher | ✅ 完成 | 2026-05-11 | 运行时依赖内存，不再需要 fs.watch |
| 2.8 新增登录窗口 | ✅ 完成 | 2026-05-09 | src/network/login/ |
| 2.9 改造启动流程 | ✅ 完成 | 2026-05-09 | 检查认证 → 登录 → 启动游戏 |
| 2.10 被踢出处理逻辑 | ✅ 完成 | 2026-05-11 | **简化版**：HTTP 401 机制，旧 Token 失效 |
| 2.11 阶段二检查点 | ✅ 完成 | 2026-05-11 | 端到端流程验证通过 |

### 阶段三：清理与文档

| 任务 | 状态 | 完成日期 | 备注 |
|------|------|----------|------|
| 3.1 删除旧代码 | ✅ 完成 | 2026-05-11 | 删除 7 个路径（约 3682 个文件） |
| 3.2 创建 Docker 开发环境 | ✅ 已就绪 | 2026-05-09 | docker-compose.yml、Dockerfile、initdb.d 已存在 |
| 3.3 更新文档 | ✅ 完成 | 2026-05-11 | README.md, AGENTS.md, NOTICE.md, CONTRIBUTING.md, SECURITY.md, CHANGELOG.md |
| 3.4 更新 CI/CD | ✅ 完成 | 2026-05-11 | 新增 test-backend job；更新 requirements.txt |
| 3.5 阶段三检查点 | ✅ 完成 | 2026-05-11 | 旧代码已删除，文档已更新，CI 已配置 |

## 重构完成状态

| 阶段 | 状态 | 完成日期 | 说明 |
|------|------|----------|------|
| 阶段 0：在线资源备份 | 待开始 | - | 风险缓解步骤（可选） |
| 阶段一：后端基础设施 | ✅ 完成 | 2026-05-09 | FastAPI + PostgreSQL 认证与数据持久化 |
| 阶段二：Electron 客户端改造 | ✅ 完成 | 2026-05-11 | HTTP 批量同步、单点登录踢出、原始代码 bug 修复 |
| 阶段三：清理与文档 | ✅ 完成 | 2026-05-11 | 旧代码删除、文档更新、CI/CD 配置 |

---

## 八、快速恢复指南

### 8.1 从零开始恢复

如果需要完全从零开始：

**方案 A：使用 initdb.d 快速启动（开发环境推荐）**

```bash
# 1. 克隆仓库
git clone <repo-url>
cd qqpet_automation

# 2. 切换到重构分支（如果有）
git checkout <feature/network-refactor>

# 3. 启动 PostgreSQL（自动执行 initdb.d 中的初始化脚本）
docker-compose up -d postgres

# 4. 准备后端环境
cd server
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 5. 启动后端（数据库已通过 initdb.d 初始化）
uvicorn app.main:app --reload

# 6. 启动 Electron 客户端（新终端）
cd ../qq-pet-macos
npm install
npx electron .
```

**方案 B：使用 Alembic 迁移（生产环境）**

```bash
# 1-4 步骤同上

# 5. 运行迁移初始化数据库
alembic upgrade head

# 6-7 步骤同上
```

### 8.2 断点恢复

如果某阶段中断，从检查点继续：

**阶段 0 中断**：
- 确认资源备份状态
- 重新下载或备份缺失的资源

**阶段一中断**：
- 确保 PostgreSQL 运行
- 如果使用 initdb.d：检查初始化脚本是否已执行
- 如果使用 Alembic：运行 `alembic current` 检查迁移状态，`alembic upgrade head` 应用剩余迁移
- 检查 API 端点是否正常工作

**阶段二中断**：
- 确保后端正常运行
- 检查 `src/network/` 目录完整性
- 检查 `$Store` 是否已替换为 `RemoteStore`
- 检查启动流程是否已改造

**阶段三中断**：
- 检查 `git status` 确认哪些文件已删除
- 检查文档更新状态
- 检查 CI/CD 配置

### 8.3 PostgreSQL 数据重置

如果需要重置数据库重新初始化：

```bash
# 停止并删除容器和数据卷
docker-compose down -v

# 重新启动（会重新执行 initdb.d 脚本）
docker-compose up -d postgres
```

### 8.4 回滚方案

如果需要回滚到本地架构版本：

```bash
# 1. 查看 git 历史
git log --oneline

# 2. 找到重构前的 commit
git checkout <commit-before-refactor>

# 3. 或使用 reflog
git reflog
git reset --hard HEAD@{n}
```

**注意**：重构涉及大量文件删除和修改，建议在重构前创建备份分支：
```bash
git checkout -b backup/before-refactor
git checkout -b feature/network-refactor
```

---

## 九、管理员用户创建

由于注册功能不开放，管理员需要手动创建用户：

### 方法一：Python 脚本

```python
# server/create_user.py
from app.database import SessionLocal
from app.core.security import get_password_hash
from app.models.user import User

def create_user(username: str, password: str, is_admin: bool = False):
    db = SessionLocal()
    try:
        hashed_password = get_password_hash(password)
        user = User(
            username=username,
            hashed_password=hashed_password,
            is_admin=is_admin
        )
        db.add(user)
        db.commit()
        print(f"用户 {username} 创建成功")
    finally:
        db.close()

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("用法: python create_user.py <username> <password> [--admin]")
        sys.exit(1)
    username = sys.argv[1]
    password = sys.argv[2]
    is_admin = "--admin" in sys.argv
    create_user(username, password, is_admin)
```

### 方法二：直接操作数据库

```sql
-- 密码哈希需要用 bcrypt 生成
-- 可以在 Python 中先生成：
-- from app.core.security import get_password_hash
-- print(get_password_hash("your-password"))

INSERT INTO users (username, hashed_password, is_admin)
VALUES ('admin', '$2b$12$...', true);
```

---

## 十、参考资料

- [FastAPI 官方文档](https://fastapi.tiangolo.com/)
- [SQLAlchemy 2.0 文档](https://docs.sqlalchemy.org/en/20/)
- [Alembic 迁移文档](https://alembic.sqlalchemy.org/)
- [PostgreSQL 文档](https://www.postgresql.org/docs/)
- [Electron 文档](https://www.electronjs.org/docs)
- [Axios 文档](https://axios-http.com/)

---

**文档结束**

> 本文档记录了从本地单用户架构到服务器-客户端多用户架构的完整重构计划。
> 实施时请按阶段顺序执行，每阶段完成后验证检查点。
