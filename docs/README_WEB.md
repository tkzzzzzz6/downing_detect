# 溺水检测系统 - Web版

本文档说明如何运行和打包前后端分离的 Web 版溺水检测系统。

## 项目结构

```
downing_detect/
├── backend/                    # 后端目录
│   ├── api/                   # API 路由
│   │   ├── detection.py      # 检测 API
│   │   ├── incidents.py      # 事件管理 API
│   │   └── config.py         # 配置管理 API
│   ├── services/              # 服务层
│   │   ├── detection_service.py
│   │   ├── incident_service.py
│   │   └── websocket_manager.py
│   ├── core/                  # 核心代码（原 src/）
│   ├── models.py              # Pydantic 数据模型
│   ├── api.py                 # FastAPI 主入口
│   └── requirements.txt       # 后端依赖
├── frontend/                  # 前端目录
│   ├── public/               # 静态资源
│   ├── src/                  # React 源码
│   │   ├── components/      # React 组件
│   │   ├── pages/           # 页面组件
│   │   ├── services/        # API 客户端
│   │   ├── App.tsx          # 主应用
│   │   └── index.tsx        # 入口文件
│   ├── electron/            # Electron 主进程
│   │   ├── main.js         # 主进程
│   │   └── preload.js      # 预加载脚本
│   ├── package.json
│   └── tsconfig.json
├── model/                     # YOLO 模型
├── config/                    # 配置文件
└── output/                    # 输出目录
```

## 环境要求

### 后端

- Python 3.8+
- **uv** 包管理器（推荐）
- PyTorch 2.4.1
- CUDA（可选，用于 GPU 加速）

### 前端

- Node.js 16+
- npm 或 yarn

## 开发模式运行

### 1. 安装 uv（如果还没安装）

```bash
# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Linux/macOS
curl -LsSf https://astral.sh/uv/install.sh | sh

# 或使用 pip
pip install uv
```

### 2. 安装后端依赖

```bash
# 在项目根目录
uv sync
```

就这么简单！uv 会自动创建虚拟环境并安装所有依赖。

### 3. 启动后端服务

```bash
# 方式1：使用 uv run（推荐）
uv run backend/api.py

# 方式2：进入 backend 目录
cd backend
uv run api.py
```

后端服务将在 `http://127.0.0.1:8000` 启动。

访问 `http://127.0.0.1:8000/docs` 可以查看 API 文档。

### 4. 安装前端依赖

```bash
# 新开一个终端，进入前端目录
cd frontend

# 安装依赖
npm install
```

### 5. 启动前端开发服务器

```bash
# 在 frontend 目录下
npm start
```

前端将在 `http://localhost:3000` 启动。

### 6. 启动 Electron（可选）

如果你想在 Electron 桌面应用中运行：

```bash
# 在 frontend 目录下
npm run electron-dev
```

这将同时启动 React 开发服务器和 Electron。

## 生产打包

### 选项1: 前端独立打包（推荐）

用户需要自己安装 Python 环境和依赖。

```bash
# 1. 构建前端
cd frontend
npm run build

# 2. 打包 Electron 应用
npm run dist
```

打包后的文件在 `frontend/dist/` 目录下。

### 使用说明

1. 用户需要先安装 Python 3.8+ 和依赖：
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. 手动启动后端服务：
   ```bash
   python api.py
   ```

3. 然后运行打包的 Electron 应用

### 选项2: 完整打包

将 Python 环境一起打包（文件较大，约 1-1.5GB）。

```bash
# 1. 使用 PyInstaller 打包后端
cd backend
pip install pyinstaller
pyinstaller --onefile api.py

# 2. 修改 frontend/electron/main.js 中的 Python 路径
# 3. 构建并打包前端
cd ../frontend
npm run build
npm run dist
```

## API 接口

### 检测管理

- `POST /api/detection/start` - 开始检测
- `POST /api/detection/stop` - 停止检测
- `GET /api/detection/status` - 获取检测状态

### 事件管理

- `GET /api/incidents` - 获取事件列表
- `GET /api/incidents/{id}` - 获取事件详情
- `GET /api/incidents/{id}/screenshot` - 获取事件截图
- `DELETE /api/incidents/{id}` - 删除事件

### 配置管理

- `GET /api/config` - 获取配置
- `PUT /api/config` - 更新配置

### WebSocket

- `WS /ws` - 实时消息推送

## 配置文件

配置文件位于 `config/settings.yaml`。

### 示例配置

```yaml
incident_output_dir: output/incidents

logging:
  level: INFO
  log_dir: logs

email:
  smtp_server: smtp.qq.com
  smtp_port: 465
  username: your-email@qq.com
  password: your-password
  sender: your-email@qq.com
  recipients:
    - recipient@example.com
  use_tls: true

vlm:
  provider: qwen
  model: qwen-vl-plus
  api_key: your-api-key
  prompt_template: "请描述画面中的溺水风险、人物位置以及环境。"
  timeout: 15
  max_retries: 2
```

## 常见问题

### 1. 后端无法启动

**问题**: 提示缺少依赖或导入错误

**解决**:
```bash
# 在项目根目录
uv sync

# 或强制重新安装
uv sync --reinstall
```

### 2. 前端无法连接后端

**问题**: WebSocket 连接失败或 API 请求超时

**解决**:
- 确保后端服务在 `http://127.0.0.1:8000` 运行
- 检查防火墙设置
- 查看浏览器控制台的错误信息

### 3. Electron 启动失败

**问题**: 提示无法启动后端服务

**解决**:
- 确保已安装 Python 和 uv
- 确保已运行 `uv sync` 安装依赖
- 设置环境变量 `PYTHON_PATH` 指向 Python 可执行文件
- 检查 `frontend/electron/main.js` 中的路径配置

### 4. 模型文件缺失

**问题**: 提示找不到 `model/best_seg.pt` 或 `model/best_detect.pt`

**解决**:
- 确保模型文件存在于 `model/` 目录
- 如果没有，需要先训练模型或从其他地方获取

## 开发指南

### 添加新的 API 端点

1. 在 `backend/api/` 下创建或修改路由文件
2. 在 `backend/models.py` 中定义请求/响应模型
3. 在 `backend/api.py` 中注册路由
4. 在 `frontend/src/services/api.ts` 中添加客户端方法

### 添加新的前端页面

1. 在 `frontend/src/pages/` 下创建新组件
2. 在 `frontend/src/App.tsx` 中添加路由
3. 在侧边栏菜单中添加导航链接

### WebSocket 消息类型

- `frame` - 帧更新
- `alert` - 告警消息
- `status` - 状态更新
- `error` - 错误消息

## 性能优化

### 后端

- 使用 `uvicorn` 的 worker 模式提高并发性能
- 启用 GPU 加速 YOLO 模型推理
- 配置合适的 VLM 超时和重试次数

### 前端

- 使用 React.memo 优化组件渲染
- 使用虚拟滚动处理大量事件列表
- 限制 WebSocket 消息频率

## 许可证

MIT License

## 支持

如有问题，请查看项目 README.md 或提交 Issue。
