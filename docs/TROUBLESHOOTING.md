# 故障排除指南

本文档帮助你解决溺水检测系统中的常见问题。

## 🔍 快速诊断

### 1. 运行导入测试

```bash
uv run test_imports.py
```

这会测试所有关键模块是否能正确导入。

### 2. 运行环境检查

```bash
uv run check_env.py
```

这会检查依赖、配置、模型文件等是否正确。

### 3. 检查后端日志

启动后端后，查看日志文件：
```bash
tail -f logs/app_*.log
```

## ❌ Network Error（网络错误）

### 症状
前端显示 "Network Error" 或 "Failed to start detection"

### 可能原因和解决方案

#### 1. 后端导入路径错误

**症状**: 后端启动后，调用 API 时崩溃

**检查**:
```bash
uv run test_imports.py
```

**解决**: 已修复。所有导入应使用 `backend.core.*` 而不是 `src.*`

#### 2. 后端未启动或崩溃

**检查**:
```bash
# 访问后端健康检查
curl http://127.0.0.1:8001/health
```

**解决**:
```bash
# 重启后端
uv run backend/api.py
```

#### 3. 端口冲突

**症状**: 后端启动失败，提示端口已被占用

**解决**:
```bash
# Windows
netstat -ano | findstr :8001
taskkill /PID <进程ID> /F

# Linux/Mac
lsof -i :8001
kill -9 <进程ID>
```

#### 4. CORS 配置问题

**症状**: 浏览器控制台显示 CORS 错误

**检查**: `backend/api.py` 中的 CORS 配置

**解决**: 确保包含前端地址：
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # 添加前端地址
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

#### 5. 缺少依赖

**检查**:
```bash
uv run check_env.py
```

**解决**:
```bash
uv sync --reinstall
```

## 📹 视频检测失败

### 症状
启动检测后立即失败或无响应

### 可能原因和解决方案

#### 1. 视频文件不存在

**检查**: 确认视频文件路径正确

**解决**: 使用绝对路径或确保相对路径正确

#### 2. 摄像头无法访问

**检查**:
```bash
uv run test/test_camera.py
```

**解决**:
- 确保摄像头已连接
- 检查摄像头权限
- 尝试不同的摄像头索引（0, 1, 2）

#### 3. 模型文件缺失

**检查**:
```bash
ls -lh model/
```

应该看到：
- `best_seg.pt` (河流分割模型)
- `best_detect.pt` (人员检测模型)

**解决**: 训练模型或从其他地方获取

#### 4. GPU/CUDA 问题

**症状**: 提示 CUDA 错误

**解决**:
```bash
# 检查 CUDA 是否可用
python -c "import torch; print(torch.cuda.is_available())"

# 如果不可用，使用 CPU 模式（会较慢）
# 模型会自动降级到 CPU
```

## 🌐 WebSocket 连接失败

### 症状
前端无法接收实时更新

### 解决方案

#### 1. 检查 WebSocket 连接

打开浏览器控制台，查看是否有 WebSocket 错误

#### 2. 防火墙设置

确保防火墙允许 WebSocket 连接（端口 8001）

#### 3. 代理问题

如果使用代理，确保 WebSocket 请求不被拦截

## 📧 邮件发送失败

### 症状
检测到溺水但未收到邮件

### 解决方案

#### 1. 检查邮件配置

编辑 `config/settings.yaml`:
```yaml
email:
  smtp_server: smtp.qq.com  # 或其他 SMTP 服务器
  smtp_port: 465
  username: your-email@qq.com
  password: your-app-password  # 注意：QQ邮箱需要使用授权码
  sender: your-email@qq.com
  recipients:
    - recipient@example.com
  use_tls: true
```

#### 2. 测试 SMTP 连接

```python
import smtplib
server = smtplib.SMTP_SSL('smtp.qq.com', 465)
server.login('your-email@qq.com', 'your-password')
server.quit()
print("SMTP 连接成功！")
```

#### 3. 常见问题

- **QQ 邮箱**: 需要使用授权码而不是登录密码
- **Gmail**: 需要开启"允许不够安全的应用"或使用应用专用密码
- **企业邮箱**: 咨询 IT 部门获取 SMTP 设置

## 🤖 VLM 调用失败

### 症状
检测到溺水但 VLM 分析失败

### 解决方案

#### 1. 检查 VLM 配置

编辑 `config/settings.yaml`:
```yaml
vlm:
  provider: qwen  # 或 openai, moonshot, ollama
  model: qwen-vl-plus
  api_key: your-api-key  # Ollama 不需要
  base_url: https://dashscope.aliyuncs.com/...  # 可选
```

#### 2. 测试 API 连接

```bash
# 测试 OpenAI
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer your-api-key"

# 测试通义千问
curl https://dashscope.aliyuncs.com/... \
  -H "Authorization: Bearer your-api-key"
```

#### 3. 本地 Ollama

如果使用 Ollama：
```bash
# 启动 Ollama
ollama serve

# 拉取模型
ollama pull llava

# 测试
ollama run llava
```

## 🎨 前端问题

### 无法连接后端

**检查**:
1. 后端是否在运行（http://127.0.0.1:8001/health）
2. 前端 API 配置是否正确（`frontend/src/services/api.ts`）

**解决**: 确保 `BACKEND_URL` 正确：
```typescript
const BACKEND_URL = 'http://127.0.0.1:8001';
```

### Electron 无法启动后端

**症状**: Electron 启动后显示"后端服务连接失败"

**解决**:
1. 设置 `PYTHON_PATH` 环境变量
2. 或手动启动后端：
   ```bash
   uv run backend/api.py
   ```
3. 然后只启动前端：
   ```bash
   cd frontend
   npm start
   ```

### npm 依赖安装失败

**解决**:
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

## 📝 日志位置

- **后端日志**: `logs/app_YYYY-MM-DD.log`
- **浏览器控制台**: 按 F12 打开开发者工具
- **Electron 日志**: 查看 Electron 控制台

## 🆘 获取更多帮助

### 1. 查看文档

- `QUICKSTART.md` - 快速开始
- `README_WEB.md` - Web 版详细说明
- `UV_GUIDE.md` - UV 使用指南
- `CLAUDE.md` - 代码架构

### 2. 运行诊断工具

```bash
# 环境检查
uv run check_env.py

# 导入测试
uv run test_imports.py

# 摄像头测试
uv run test/test_camera.py
```

### 3. 检查系统状态

```bash
# 后端健康检查
curl http://127.0.0.1:8001/health

# API 文档
open http://127.0.0.1:8001/docs
```

### 4. 常用命令

```bash
# 重装依赖
uv sync --reinstall

# 清除缓存
uv cache clean && uv sync

# 重启后端
uv run backend/api.py

# 重启前端
cd frontend && npm start
```

## 📊 性能问题

### CPU 使用率过高

**原因**: YOLO 模型推理耗费资源

**解决**:
- 使用 GPU 加速
- 降低视频分辨率
- 减少帧率

### 内存占用过大

**解决**:
- 关闭不必要的检测会话
- 清理旧的事件记录
- 重启后端服务

## 🔧 重置环境

如果问题无法解决，尝试完全重置：

```bash
# 1. 删除虚拟环境
rm -rf .venv

# 2. 清除 uv 缓存
uv cache clean

# 3. 重新安装依赖
uv sync

# 4. 删除前端依赖
cd frontend
rm -rf node_modules
npm install

# 5. 重启所有服务
```

---

如果以上方法都无法解决问题，请：
1. 查看日志文件
2. 记录错误信息
3. 提交 Issue 并附上详细信息
