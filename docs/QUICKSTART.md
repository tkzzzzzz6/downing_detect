# 快速开始指南

本指南帮助你快速启动溺水检测系统的 Web 版本。

## 前置要求

### 后端

- Python 3.12 或更高版本
- **uv** 包管理器（推荐，比 pip 快 10-100 倍）
- 已安装 CUDA（可选，用于 GPU 加速）

### 前端

- Node.js 16 或更高版本
- npm 或 yarn

## 快速安装

### 0. 安装 uv（如果还没安装）

```bash
# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Linux/macOS
curl -LsSf https://astral.sh/uv/install.sh | sh

# 或使用 pip
pip install uv
```

### 1. 安装后端依赖

```bash
# 在项目根目录
uv sync

# 就这么简单！uv 会自动创建虚拟环境并安装所有依赖
```

### 2. 安装前端依赖

```bash
cd frontend
npm install
```

## 快速启动

### 方式一：使用脚本（推荐）

#### Windows

双击运行：
- `start_backend.bat` - 启动后端服务（使用 uv）

然后：
```bash
cd frontend
npm run electron-dev
```

#### Linux/Mac

```bash
# 添加执行权限（首次运行）
chmod +x start_backend.sh

# 启动后端
./start_backend.sh
```

然后在另一个终端：
```bash
cd frontend
npm run electron-dev
```

### 方式二：手动启动

#### 终端1 - 后端

```bash
# 在项目根目录或 backend 目录
uv run backend/api.py

# 或者
cd backend
uv run api.py
```

等待看到：
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

#### 终端2 - 前端

```bash
cd frontend
npm start
```

浏览器会自动打开 `http://localhost:3000`

#### （可选）启动 Electron

如果你想使用桌面应用：

```bash
cd frontend
npm run electron-dev
```

## 验证安装

1. 后端健康检查：访问 `http://127.0.0.1:8000/health`
   应该看到：`{"status":"healthy","message":"Backend service is running"}`

2. API 文档：访问 `http://127.0.0.1:8000/docs`
   应该看到 Swagger UI 界面

3. 前端界面：访问 `http://localhost:3000`
   应该看到溺水检测系统的界面

## 使用步骤

1. **配置系统**
   - 点击侧边栏的「系统设置」
   - 配置邮件服务器（如果需要邮件通知）
   - 配置 VLM（如果需要 AI 分析）

2. **开始检测**
   - 点击侧边栏的「实时检测」
   - 选择视频源类型：视频文件 或 摄像头
   - 输入视频文件路径或选择摄像头索引
   - 点击「开始检测」按钮

3. **查看事件**
   - 点击侧边栏的「事件历史」
   - 浏览、查看、删除检测到的事件

## 常见问题

### 后端无法启动

**错误**：`ModuleNotFoundError: No module named 'fastapi'`

**解决**：
```bash
# 在项目根目录
uv sync

# 或者强制重新安装
uv sync --reinstall
```

### 前端无法连接后端

**错误**：前端显示「连接失败」

**解决**：
1. 确认后端已启动：访问 `http://127.0.0.1:8000/health`
2. 检查防火墙设置
3. 查看后端终端的错误信息

### 模型文件缺失

**错误**：`FileNotFoundError: model/best_seg.pt not found`

**解决**：
确保 `model/` 目录下有以下文件：
- `best_seg.pt` - 河流分割模型
- `best_detect.pt` - 人员检测模型

如果没有，需要先训练模型或从其他地方获取。

### Electron 启动失败

**错误**：Electron 无法启动 Python 后端

**解决**：
1. 设置环境变量 `PYTHON_PATH` 指向 Python 可执行文件
2. 或者手动启动后端，然后只运行前端：
   ```bash
   cd frontend
   npm start
   ```

## 下一步

- 查看 `README_WEB.md` 了解详细的开发和打包说明
- 查看 `design.md` 了解系统架构设计
- 查看 `CLAUDE.md` 了解代码结构和开发指南

## 获取帮助

如果遇到问题，请检查：
1. 后端日志：`logs/` 目录
2. 浏览器控制台：按 F12 查看
3. 后端 API 文档：`http://127.0.0.1:8000/docs`

祝使用愉快！
