# AGENTS.md

## 项目概览

混合项目，包含三个组件：
- **Electron 桌面应用**: `qq-pet-macos/` - QQ 宠物游戏（怀旧服 v1.2.4）移植版，使用 Ruffle WASM
- **FastAPI 后端**: `server/` - 认证服务、数据持久化、多设备同步（HTTP API）
- **Docker 开发环境**: `docker-compose.yml` - PostgreSQL + 后端服务编排

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
- **数据同步机制** - HTTP PATCH + 1秒去抖批量同步（RemoteStore 实现），WebSocket 已移除
- **单点登录踢出** - 新登录使旧会话 `is_active=false`，客户端通过 HTTP 401 检测并刷新 Token，刷新失败则显示登录窗口
- **存储方案** - 运行时依赖内存（RemoteStore.cache），不再使用 `fs.watch` 监听本地文件
- **CI 触发条件** - 仅在 `v*` 标签或 `workflow_dispatch` 时构建
- **macOS 未签名应用** - 需要执行：`sudo xattr -rd com.apple.quarantine /Applications/QQ宠物.app`
- **面向用户的语言** - 所有 README 和文档均使用**中文**
- **服务器地址配置** - 硬编码默认 `http://localhost:8000`，可通过 electron-store 修改

## 代码规范

- **提交信息**: 约定式提交风格：`feat(cli):`、`fix(sync):`、`docs(readme):`
- **Python**: 必须使用类型注解，路径使用 `pathlib.Path`，不允许原地修改
- **JavaScript**: 使用 `const`/`let`（禁用 `var`），使用 `async/await`
- **分支命名**: `feat/xxx`、`fix/xxx`、`docs/xxx`

## 相关文件

- `.github/workflows/build.yml` - CI/CD 在 `v*` 标签时构建 macOS/Windows/Linux 版本 + 后端测试
- `server/app/main.py` - FastAPI 入口
- `server/app/models/` - SQLAlchemy 数据模型
- `server/app/api/` - API 路由
- `server/initdb.d/` - PostgreSQL 初始化脚本（开发环境）
- `qq-pet-macos/src/ini/remoteStore.js` - 客户端远程存储同步
- `qq-pet-macos/src/network/` - 客户端网络层（api.js, auth.js, login 窗口）
