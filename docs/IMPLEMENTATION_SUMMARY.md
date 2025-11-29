# 前后端分离架构实现总结

本文档总结了溺水检测系统前后端分离架构的实现情况。

## 已完成的工作

### ✅ 1. 项目结构重组

创建了清晰的前后端目录结构：

```
downing_detect/
├── backend/                    # 后端 FastAPI 服务
│   ├── api/                   # API 路由模块
│   │   ├── __init__.py
│   │   ├── detection.py      # 检测管理 API
│   │   ├── incidents.py      # 事件管理 API
│   │   └── config.py         # 配置管理 API
│   ├── services/              # 业务逻辑层
│   │   ├── __init__.py
│   │   ├── detection_service.py
│   │   ├── incident_service.py
│   │   └── websocket_manager.py
│   ├── core/                  # 核心模块（从 src/ 迁移）
│   ├── models.py              # Pydantic 数据模型
│   ├── api.py                 # FastAPI 主入口
│   ├── __init__.py
│   └── requirements.txt       # 后端依赖
└── frontend/                  # 前端 Electron + React 应用
    ├── public/
    │   └── index.html
    ├── src/
    │   ├── pages/
    │   │   ├── DetectionPage.tsx
    │   │   ├── IncidentPage.tsx
    │   │   └── SettingsPage.tsx
    │   ├── services/
    │   │   └── api.ts
    │   ├── App.tsx
    │   └── index.tsx
    ├── electron/
    │   ├── main.js
    │   └── preload.js
    ├── package.json
    └── tsconfig.json
```

### ✅ 2. 后端 FastAPI 服务

#### API 端点

**检测管理** (`/api/detection/*`)
- `POST /api/detection/start` - 启动检测会话
- `POST /api/detection/stop` - 停止检测会话
- `GET /api/detection/status` - 获取检测状态

**事件管理** (`/api/incidents/*`)
- `GET /api/incidents` - 分页获取事件列表
- `GET /api/incidents/{id}` - 获取事件详情
- `GET /api/incidents/{id}/screenshot` - 获取事件截图
- `DELETE /api/incidents/{id}` - 删除事件

**配置管理** (`/api/config/*`)
- `GET /api/config` - 获取配置（敏感数据已屏蔽）
- `PUT /api/config` - 更新配置

**WebSocket** (`/ws`)
- 实时推送帧更新、告警、状态和错误消息

#### 服务层

- **DetectionService**: 管理检测会话，确保同一时间只有一个检测任务
- **IncidentService**: 管理事件记录的 CRUD 操作和持久化
- **WebSocketManager**: 管理 WebSocket 连接和消息广播

### ✅ 3. 前端 Electron + React 应用

#### 主要功能

- **实时检测页面**: 配置视频源、启动/停止检测、查看实时状态和告警
- **事件历史页面**: 浏览事件记录、查看详情、删除事件
- **系统设置页面**: 配置邮件、VLM 和日志参数

#### 技术栈

- React 18 + TypeScript
- Material-UI 组件库
- React Router 路由管理
- Axios HTTP 客户端
- WebSocket 实时通信
- Electron 桌面应用框架

### ✅ 4. 完整文档

- **README_WEB.md**: Web 版详细使用说明
- **QUICKSTART.md**: 快速开始指南
- **CLAUDE.md**: 更新了 Web 架构说明
- **design.md**: 架构设计文档（已存在）
- **IMPLEMENTATION_SUMMARY.md**: 本文档

### ✅ 5. 启动脚本

- `start_backend.bat` (Windows)
- `start_backend.sh` (Linux/Mac)

## 下一步操作

### 立即可以做的

#### 1. 安装依赖

**安装 uv（推荐）：**
```bash
# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Linux/macOS
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**后端：**
```bash
# 在项目根目录
uv sync
```

**前端：**
```bash
cd frontend
npm install
```

#### 2. 启动开发服务器

**后端：**
```bash
# 方式1：从项目根目录
uv run backend/api.py

# 方式2：使用启动脚本
./start_backend.sh  # Linux/Mac
start_backend.bat   # Windows
```

**前端（React）：**
```bash
cd frontend
npm start
```

**前端（Electron）：**
```bash
cd frontend
npm run electron-dev
```

#### 3. 测试 API

访问 `http://127.0.0.1:8000/docs` 查看 Swagger UI 并测试 API。

### 需要注意的事项

#### ⚠️ 1. 使用 uv 管理依赖

本项目使用 `uv` 作为包管理器，配置在 `pyproject.toml` 中：

```bash
# 安装依赖
uv sync

# 运行脚本
uv run <script.py>

# 添加新依赖
uv add <package-name>
```

详见 `UV_GUIDE.md` 获取完整的 uv 使用说明。

#### ⚠️ 2. 后端导入路径

后端代码现在在 `backend/` 目录下，所有导入都使用 `backend.` 前缀：

```python
# 正确
from backend.core.settings import load_settings
from backend.services.websocket_manager import ws_manager

# 错误
from src.settings import load_settings
from services.websocket_manager import ws_manager
```

#### ⚠️ 3. 配置文件

确保 `config/settings.yaml` 文件存在。如果不存在，复制示例文件：

```bash
cp config/settings.example.yaml config/settings.yaml
# 然后编辑 config/settings.yaml 填写实际配置
```

#### ⚠️ 4. 模型文件

确保 `model/` 目录下有训练好的模型：
- `model/best_seg.pt` - 河流分割模型
- `model/best_detect.pt` - 人员检测模型

#### ⚠️ 5. Python 路径配置

如果 Electron 无法启动后端，设置环境变量：

```bash
# Windows
set PYTHON_PATH=C:\Path\To\Python\python.exe

# Linux/Mac
export PYTHON_PATH=/usr/bin/python3
```

或修改 `frontend/electron/main.js` 中的 Python 路径。

## 可能需要调试的地方

### 1. VideoProcessor 与 WebSocket 集成

`backend/services/detection_service.py` 中的 `WebSocketVideoProcessor` 类继承了 `VideoProcessor`，但实际的 WebSocket 更新发送逻辑还需要完善。

**当前状态**: 基础结构已创建
**需要做**: 在 `process_video` 方法中添加实时帧数据的 WebSocket 推送

### 2. IncidentManager 回调注册

确保 IncidentManager 的事件被正确保存到 IncidentService 的持久化存储中。

**建议**: 在 `detection_service.py` 中注册 `incident_manager.create_incident` 的回调到 `incident_service.add_incident`

### 3. 前端错误处理

前端的错误处理已经基本实现，但可以进一步优化：
- 添加更详细的错误提示
- 实现错误重试机制
- 添加加载动画

### 4. WebSocket 断线重连

前端已实现基础的自动重连（3秒延迟），可以考虑：
- 指数退避重连策略
- 重连次数限制
- 重连状态提示

## 打包部署

### 前端独立打包（推荐）

用户需要自己安装 Python 环境：

```bash
cd frontend
npm run build
npm run dist
```

打包后的文件在 `frontend/dist/` 目录。

### 完整打包（实验性）

包含 Python 运行时，文件较大（~1-1.5GB）：

```bash
# 1. 打包后端
cd backend
pip install pyinstaller
pyinstaller --onefile api.py

# 2. 打包前端
cd ../frontend
npm run build
npm run dist
```

需要修改 `frontend/electron/main.js` 使用打包后的 Python 可执行文件。

## 兼容性说明

### CLI 模式仍然可用

原有的命令行模式（`main.py`）仍然完全可用：

```bash
python main.py
```

CLI 模式和 Web 模式共享核心代码（现在位于 `backend/core/`），互不影响。

### 配置文件共享

两种模式使用相同的配置文件 `config/settings.yaml`。

## 测试清单

在发布前，建议测试以下功能：

- [ ] 后端服务正常启动
- [ ] API 文档可访问（http://127.0.0.1:8000/docs）
- [ ] WebSocket 连接成功
- [ ] 启动检测（视频文件）
- [ ] 启动检测（摄像头）
- [ ] 停止检测
- [ ] 查看检测状态
- [ ] 溺水告警触发
- [ ] 事件记录创建
- [ ] 事件列表显示
- [ ] 事件详情查看
- [ ] 事件截图显示
- [ ] 事件删除
- [ ] 配置读取
- [ ] 配置更新
- [ ] VLM 集成（如果启用）
- [ ] 邮件通知（如果启用）
- [ ] Electron 应用启动
- [ ] 前端打包

## 性能优化建议

### 后端

1. 使用 Uvicorn workers 提高并发性能：
   ```bash
   uvicorn backend.api:app --workers 4
   ```

2. 启用 GPU 加速（如果有 NVIDIA GPU）：
   - 安装 CUDA 版本的 PyTorch
   - 确保 YOLO 模型在 GPU 上运行

3. 调整 WebSocket 消息频率：
   - 不需要每帧都发送更新
   - 可以每 0.5 秒或 1 秒发送一次状态更新

### 前端

1. 使用 React.memo 优化重复渲染
2. 虚拟滚动大量事件列表
3. 图片懒加载
4. 缓存 API 响应

## 已知限制

1. **单会话限制**: 同一时间只能运行一个检测任务
2. **WebSocket 容量**: 未限制最大连接数
3. **事件存储**: 使用 JSON 文件，大量事件时性能可能下降
4. **视频显示**: 前端目前不显示实时视频帧（只显示状态）

## 贡献指南

如果你想继续开发或改进系统：

1. 阅读 `CLAUDE.md` 了解代码结构
2. 阅读 `design.md` 了解架构设计
3. 遵循现有的代码风格
4. 添加适当的日志和错误处理
5. 更新相关文档

## 许可证

MIT License

## 联系方式

如有问题或建议，请提交 Issue 或 Pull Request。

---

**实现完成时间**: 2025年

**实现版本**: Web v1.0.0

**实现者**: Claude Code

祝使用愉快！ 🎉
