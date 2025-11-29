# UV 使用指南

本项目使用 [uv](https://github.com/astral-sh/uv) 作为 Python 包管理器。uv 是一个极快的 Python 包安装器和解析器，可以替代 pip 和 virtualenv。

## 为什么使用 UV？

- ⚡ **极快**: 比 pip 快 10-100 倍
- 🔒 **可靠**: 确定性依赖解析
- 🎯 **简单**: 统一的工具链
- 📦 **兼容**: 支持 pyproject.toml

## 安装 UV

### Windows

```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Linux/macOS

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 使用 pip

```bash
pip install uv
```

## 常用命令

### 1. 同步依赖

安装 `pyproject.toml` 中定义的所有依赖：

```bash
uv sync
```

### 2. 安装单个包

```bash
# 安装并添加到 pyproject.toml
uv add <package-name>

# 只安装不修改 pyproject.toml
uv pip install <package-name>
```

### 3. 运行 Python 脚本

```bash
# 在虚拟环境中运行
uv run python script.py

# 或者
uv run script.py
```

### 4. 运行后端服务

```bash
cd backend
uv run api.py
```

### 5. 运行 CLI 版本

```bash
uv run main.py
```

### 6. 创建虚拟环境（可选）

uv 会自动管理虚拟环境，但如果需要手动创建：

```bash
uv venv
```

激活虚拟环境：

```bash
# Windows
.venv\Scripts\activate

# Linux/macOS
source .venv/bin/activate
```

### 7. 查看已安装的包

```bash
uv pip list
```

### 8. 更新依赖

```bash
# 更新所有依赖
uv sync --upgrade

# 更新特定包
uv add <package-name> --upgrade
```

## 项目设置

### 首次设置

1. 安装 uv（见上文）

2. 克隆项目：
   ```bash
   git clone <repository-url>
   cd downing_detect
   ```

3. 同步依赖：
   ```bash
   uv sync
   ```

4. 运行项目：
   ```bash
   # CLI 模式
   uv run main.py

   # Web 后端
   cd backend
   uv run api.py
   ```

### 开发工作流

```bash
# 添加新依赖
uv add package-name

# 运行测试
uv run pytest

# 运行后端
uv run backend/api.py

# 运行 CLI
uv run main.py
```

## 与传统工具对比

| 操作 | pip/venv | uv |
|------|----------|-----|
| 创建虚拟环境 | `python -m venv venv` | `uv venv` (自动) |
| 激活虚拟环境 | `source venv/bin/activate` | 不需要 |
| 安装依赖 | `pip install -r requirements.txt` | `uv sync` |
| 添加包 | `pip install pkg && pip freeze > requirements.txt` | `uv add pkg` |
| 运行脚本 | `python script.py` | `uv run script.py` |

## pyproject.toml 配置

项目的所有依赖都定义在根目录的 `pyproject.toml` 中：

```toml
[project]
name = "downing-detect"
version = "1.0.0"
requires-python = ">=3.8"
dependencies = [
    "fastapi==0.109.0",
    "torch==2.4.1",
    # ... 其他依赖
]
```

## 常见问题

### Q: uv sync 失败怎么办？

A: 尝试清除缓存：
```bash
uv cache clean
uv sync
```

### Q: 如何指定 Python 版本？

A: uv 会自动使用系统中的 Python，或者指定：
```bash
uv venv --python 3.10
```

### Q: 如何在 CI/CD 中使用？

A: 示例 GitHub Actions：
```yaml
- name: Install uv
  run: curl -LsSf https://astral.sh/uv/install.sh | sh

- name: Install dependencies
  run: uv sync

- name: Run tests
  run: uv run pytest
```

### Q: uv 和 pip 冲突吗？

A: 不冲突。uv 可以与 pip 并存，但建议统一使用一种工具。

### Q: 如何锁定依赖版本？

A: uv 会自动生成 `uv.lock` 文件（类似 `poetry.lock`），提交到版本控制。

## 性能提示

1. **使用缓存**: uv 有全局缓存，相同的包只下载一次
2. **并行安装**: uv 自动并行安装依赖
3. **增量更新**: `uv sync` 只更新变化的部分

## 迁移到 UV

如果你之前使用 pip + requirements.txt：

```bash
# 从 requirements.txt 迁移
uv add $(cat requirements.txt)

# 或者让 uv 自动转换
uv pip install -r requirements.txt
```

## 更多资源

- [uv 官方文档](https://github.com/astral-sh/uv)
- [pyproject.toml 规范](https://packaging.python.org/en/latest/specifications/declaring-project-metadata/)

## 本项目的 UV 命令速查

```bash
# 安装依赖
uv sync

# 运行 CLI 版本
uv run main.py

# 运行 Web 后端
cd backend && uv run api.py

# 运行训练
uv run train.py

# 添加新依赖
uv add <package-name>

# 查看依赖
uv pip list

# 更新依赖
uv sync --upgrade
```

---

**提示**: 使用 `uv --help` 查看所有可用命令。
