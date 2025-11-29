# 溺水检测系统 - 使用指南

欢迎使用溺水检测系统！本文档提供快速导航。

## 🚀 快速开始（3步）

1. **安装 uv**（推荐的包管理器）
   ```bash
   # Windows
   powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

   # Linux/macOS
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **安装依赖**
   ```bash
   uv sync
   ```

3. **运行程序**
   ```bash
   # CLI 模式（原版）
   uv run main.py

   # Web 模式（新版）
   uv run backend/api.py
   ```

## 📚 文档导航

### 新手必读

- **[快速开始指南](QUICKSTART.md)** ⭐ - 5分钟上手
- **[UV 使用指南](UV_GUIDE.md)** - uv 包管理器详细说明
- **[UV 迁移说明](UV_MIGRATION.md)** - 从 pip 迁移到 uv

### Web 版本

- **[Web 版 README](README_WEB.md)** - 前后端分离架构详细说明
- **[实现总结](IMPLEMENTATION_SUMMARY.md)** - 完整实现文档

### 开发者

- **[CLAUDE.md](CLAUDE.md)** - 代码架构和开发指南
- **[设计文档](design.md)** - 系统架构设计

## 🎯 使用模式

本系统支持两种运行模式：

### 1. CLI 模式（命令行）

原始的命令行交互式模式：

```bash
uv run main.py
```

- ✅ 简单快速
- ✅ 适合测试和演示
- ✅ 无需额外配置

### 2. Web 模式（图形界面）

现代化的 Web 界面 + Electron 桌面应用：

```bash
# 启动后端
uv run backend/api.py

# 启动前端（另一个终端）
cd frontend
npm install
npm start

# 或启动 Electron 桌面应用
npm run electron-dev
```

- ✅ 美观的图形界面
- ✅ 实时监控
- ✅ 事件管理
- ✅ 配置界面

## ⚡ 常用命令

### 后端（Python）

```bash
# 运行 CLI 模式
uv run main.py

# 运行 Web 后端
uv run backend/api.py

# 训练模型
uv run train.py

# 测试摄像头
uv run test/test_camera.py

# 添加新依赖
uv add package-name

# 查看已安装的包
uv pip list
```

### 前端（Node.js）

```bash
cd frontend

# 安装依赖
npm install

# 开发模式（React）
npm start

# 开发模式（Electron）
npm run electron-dev

# 生产构建
npm run build

# 打包桌面应用
npm run dist
```

## 📂 项目结构

```
downing_detect/
├── backend/              # FastAPI 后端服务
├── frontend/             # React + Electron 前端
├── src/                  # 核心检测代码（已迁移到 backend/core/）
├── model/               # YOLO 模型文件
├── config/              # 配置文件
├── output/              # 输出结果
├── pyproject.toml       # Python 依赖配置
├── main.py              # CLI 模式入口
└── 各种文档.md
```

## 🔧 配置

1. 复制示例配置：
   ```bash
   cp config/settings.example.yaml config/settings.yaml
   ```

2. 编辑 `config/settings.yaml`：
   - 邮件配置（SMTP）
   - VLM 配置（AI 分析）
   - 日志配置

## ❓ 常见问题

### 1. 找不到模块

```bash
# 重新同步依赖
uv sync --reinstall
```

### 2. 端口被占用

Web 后端默认使用 8001 端口，前端使用 3000 端口。修改方法：

```bash
# 后端
uv run backend/api.py --port 8001

# 前端：修改 frontend/package.json 中的 PORT
```

### 3. 模型文件缺失

确保 `model/` 目录下有：
- `best_seg.pt` - 河流分割模型
- `best_detect.pt` - 人员检测模型

### 4. GPU 加速

如果有 NVIDIA GPU：
```bash
# 安装 CUDA 版本的 PyTorch
uv add torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

## 📊 API 文档

Web 模式启动后，访问：
- **API 文档**: http://127.0.0.1:8001/docs
- **健康检查**: http://127.0.0.1:8001/health
- **前端界面**: http://localhost:3000

## 🎓 学习路径

1. **入门**: 阅读 `QUICKSTART.md`，运行 CLI 模式
2. **进阶**: 阅读 `README_WEB.md`，尝试 Web 模式
3. **开发**: 阅读 `CLAUDE.md`，了解代码结构
4. **优化**: 阅读 `UV_GUIDE.md`，掌握 uv 工具

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

开发前请阅读：
- `CLAUDE.md` - 代码规范和架构
- `design.md` - 设计理念

## 📝 许可证

MIT License

## 🆘 获取帮助

1. 查看相关文档
2. 检查日志文件 `logs/`
3. 查看 API 文档 `/docs`
4. 提交 Issue

## 🎉 开始使用

```bash
# 一键安装并运行
uv sync && uv run main.py
```

祝使用愉快！

---

**版本**: v1.0.0
**最后更新**: 2025-11-28
**维护者**: 溺水检测系统团队
