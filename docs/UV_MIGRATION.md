# UV 迁移说明

本项目已迁移至使用 **uv** 包管理器。

## 什么是 uv？

[uv](https://github.com/astral-sh/uv) 是一个极快的 Python 包安装器和解析器，用 Rust 编写：

- ⚡ **速度快**: 比 pip 快 10-100 倍
- 🔒 **可靠**: 确定性依赖解析
- 🎯 **简单**: 统一的命令行工具
- 📦 **兼容**: 完全兼容 pip 和 pyproject.toml

## 主要变更

### 1. 依赖管理

**之前（使用 pip）：**
```bash
pip install -r requirements.txt
```

**现在（使用 uv）：**
```bash
uv sync
```

### 2. 运行脚本

**之前：**
```bash
python main.py
python backend/api.py
```

**现在：**
```bash
uv run main.py
uv run backend/api.py
```

### 3. 添加依赖

**之前：**
```bash
pip install package-name
pip freeze > requirements.txt
```

**现在：**
```bash
uv add package-name  # 自动更新 pyproject.toml
```

### 4. 文件变更

- ✅ 添加：`pyproject.toml` - 所有依赖都在这里定义
- ✅ 添加：`UV_GUIDE.md` - uv 详细使用指南
- ✅ 更新：`start_backend.bat` / `start_backend.sh` - 使用 `uv run`
- ✅ 更新：所有文档（QUICKSTART.md, README_WEB.md 等）
- ❌ 删除：`backend/requirements.txt` - 不再需要

## 快速开始

### 1. 安装 uv

```bash
# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Linux/macOS
curl -LsSf https://astral.sh/uv/install.sh | sh

# 或使用 pip
pip install uv
```

### 2. 安装项目依赖

```bash
# 在项目根目录
uv sync
```

### 3. 运行项目

```bash
# CLI 模式
uv run main.py

# Web 后端
uv run backend/api.py

# 或使用脚本
./start_backend.sh  # Linux/Mac
start_backend.bat   # Windows
```

## 为什么迁移到 uv？

1. **极快的安装速度**: uv 可以在几秒内安装几十个包
2. **更好的依赖管理**: 自动解析和锁定依赖版本
3. **简化工作流**: 不需要手动管理 requirements.txt
4. **现代化**: pyproject.toml 是 Python 社区的新标准
5. **开发体验**: `uv run` 自动管理虚拟环境，无需手动激活

## 迁移检查清单

如果你是从旧版本迁移：

- [ ] 安装 uv
- [ ] 运行 `uv sync` 安装依赖
- [ ] 删除旧的 `venv` 目录（可选）
- [ ] 使用 `uv run` 替代 `python`
- [ ] 阅读 `UV_GUIDE.md` 了解更多命令

## 常见问题

### Q: 我还能使用 pip 吗？

A: 可以，但不推荐混用。建议统一使用 uv 来获得最佳体验。

### Q: uv 会创建虚拟环境吗？

A: 是的，uv 会自动在项目目录下创建 `.venv` 虚拟环境。

### Q: 如何查看安装了哪些包？

A: 使用 `uv pip list`

### Q: pyproject.toml 在哪里？

A: 项目根目录。所有依赖都定义在这个文件中。

### Q: 出现依赖冲突怎么办？

A: uv 会自动解决依赖冲突。如果还有问题：
```bash
uv cache clean
uv sync --reinstall
```

### Q: 如何升级依赖？

A:
```bash
# 升级所有依赖
uv sync --upgrade

# 升级特定包
uv add package-name --upgrade
```

## 性能对比

实测在本项目中的安装速度对比：

| 工具 | 安装时间 | 说明 |
|------|---------|------|
| pip | ~2-3 分钟 | 首次安装 |
| pip (cached) | ~30-60 秒 | 使用缓存 |
| uv | ~10-15 秒 | 首次安装 |
| uv (cached) | ~2-3 秒 | 使用缓存 |

## 更多资源

- **UV 官方文档**: https://github.com/astral-sh/uv
- **项目 UV 使用指南**: `UV_GUIDE.md`
- **快速开始**: `QUICKSTART.md`
- **Web 版说明**: `README_WEB.md`

## 反馈

如果在使用 uv 时遇到问题，请：

1. 查看 `UV_GUIDE.md`
2. 尝试 `uv sync --reinstall`
3. 查看 uv 官方文档
4. 提交 Issue

---

**迁移日期**: 2025-11-28

**版本**: v1.0.0

祝你使用愉快！ 🚀
