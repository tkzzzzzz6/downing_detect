# Design Document

## Overview

本设计文档描述了如何将溺水检测系统从命令行应用改造为前后端分离的 Web 应用架构。设计采用 FastAPI 作为后端框架，Electron 作为前端桌面应用框架，通过 REST API 和 WebSocket 进行通信。

核心设计原则：
- 最小改动：尽量保留现有 Python 代码结构
- 异步处理：视频检测在后台线程运行，不阻塞 API 响应
- 实时通信：使用 WebSocket 推送检测结果
- 用户友好：提供直观的图形界面
- 易于部署：支持独立打包和分发

## Architecture

### 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                    Electron Desktop App                      │
│                                                               │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Renderer Process (Frontend UI)                        │ │
│  │  - React Components                                    │ │
│  │  - Real-time Video Display                             │ │
│  │  - Alert Notifications                                 │ │
│  │  - Incident Management                                 │ │
│  │  - Settings Configuration                              │ │
│  └──────────────────┬─────────────────────────────────────┘ │
│                     │                                         │
│  ┌──────────────────▼─────────────────────────────────────┐ │
│  │  Main Process (Node.js)                                │ │
│  │  - Window Management                                   │ │
│  │  - Backend Process Management                          │ │
│  │  - IPC Communication                                   │ │
│  └──────────────────┬─────────────────────────────────────┘ │
└────────────────────┼───────────────────────────────────────┘
                     │
                     │ HTTP REST API / WebSocket
                     │ http://127.0.0.1:8001
                     │
┌────────────────────▼───────────────────────────────────────┐
│              FastAPI Backend Service                        │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  API Layer                                            │  │
│  │  - REST Endpoints (/api/*)                           │  │
│  │  - WebSocket Endpoint (/ws)                          │  │
│  │  - Request Validation                                │  │
│  │  - Response Serialization                            │  │
│  └──────────────────┬───────────────────────────────────┘  │
│                     │                                        │
│  ┌──────────────────▼───────────────────────────────────┐  │
│  │  Service Layer                                        │  │
│  │  - DetectionService (manages video processing)       │  │
│  │  - IncidentService (manages incident records)        │  │
│  │  - ConfigService (manages configuration)             │  │
│  │  - WebSocketManager (manages WS connections)         │  │
│  └──────────────────┬───────────────────────────────────┘  │
│                     │                                        │
│  ┌──────────────────▼───────────────────────────────────┐  │
│  │  Existing Core Modules (Minimal Changes)             │  │
│  │  - VideoProcessor                                     │  │
│  │  - IncidentManager                                    │  │
│  │  - VLMWorker                                          │  │
│  │  - EmailNotifier                                      │  │
│  │  - ModelLoader                                        │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 数据流

**检测启动流程**:
```
User Click "Start" 
  → Frontend sends POST /api/detection/start
  → Backend creates DetectionSession
  → Backend starts VideoProcessor in background thread
  → Backend returns session_id
  → Frontend connects to WebSocket /ws
  → VideoProcessor sends frames → WebSocket → Frontend displays
```

**告警流程**:
```
VideoProcessor detects danger
  → IncidentManager creates incident
  → WebSocketManager broadcasts alert
  → Frontend displays alert notification
  → EmailNotifier sends email (if configured)
```

## Components and Interfaces

### 1. Backend API Endpoints

#### 1.1 Detection Management

```python
# POST /api/detection/start
Request:
{
  "video_source": "path/to/video.mp4" | 0,  # file path or camera index
  "is_webcam": false
}

Response:
{
  "session_id": "uuid",
  "status": "started",
  "message": "Detection started successfully"
}
```

```python
# POST /api/detection/stop
Response:
{
  "status": "stopped",
  "statistics": {
    "total_frames": 1250,
    "processing_time": 125.5,
    "incidents_detected": 3
  }
}
```

```python
# GET /api/detection/status
Response:
{
  "status": "running" | "idle" | "stopping",
  "session_id": "uuid" | null,
  "current_frame": 1250,
  "fps": 10.2,
  "elapsed_time": 125.5,
  "video_source": "demo.mp4"
}
```

#### 1.2 Incident Management

```python
# GET /api/incidents?page=1&limit=20&start_date=2024-01-01&end_date=2024-12-31
Response:
{
  "total": 45,
  "page": 1,
  "limit": 20,
  "incidents": [
    {
      "incident_id": "uuid",
      "camera_id": "demo.mp4",
      "timestamp": 1701234567.89,
      "overlap_ratio": 0.95,
      "screenshot_url": "/api/incidents/uuid/screenshot",
      "vlm_summary": "Person in water, high risk",
      "status": "notified"
    }
  ]
}
```

```python
# GET /api/incidents/{incident_id}
Response:
{
  "incident_id": "uuid",
  "camera_id": "demo.mp4",
  "frame_id": 1250,
  "timestamp": 1701234567.89,
  "overlap_ratio": 0.95,
  "bbox": [100, 200, 300, 400],
  "screenshot_url": "/api/incidents/uuid/screenshot",
  "vlm_summary": "Person in water, high risk",
  "vlm_confidence": 0.92,
  "status": "notified",
  "extra_metadata": {}
}
```

```python
# GET /api/incidents/{incident_id}/screenshot
Response: Binary image data (PNG)
```

```python
# DELETE /api/incidents/{incident_id}
Response:
{
  "status": "deleted",
  "message": "Incident deleted successfully"
}
```

#### 1.3 Configuration Management

```python
# GET /api/config
Response:
{
  "incident_output_dir": "output/incidents",
  "email": {
    "smtp_server": "smtp.qq.com",
    "smtp_port": 465,
    "username": "user@example.com",
    "sender": "user@example.com",
    "recipients": ["admin@example.com"],
    "use_tls": true,
    "enabled": true
  },
  "vlm": {
    "provider": "qwen",
    "model": "qwen-vl-flash",
    "api_key": "***",  # masked
    "base_url": "https://...",
    "prompt_template": "...",
    "timeout": 15.0,
    "max_retries": 2,
    "enabled": true
  },
  "logging": {
    "level": "INFO",
    "log_dir": "logs"
  }
}
```

```python
# PUT /api/config
Request:
{
  "email": {
    "recipients": ["new@example.com"]
  },
  "vlm": {
    "timeout": 20.0
  }
}

Response:
{
  "status": "updated",
  "message": "Configuration updated successfully"
}
```

#### 1.4 WebSocket Protocol

```python
# WebSocket /ws
# Client → Server (optional, for future control)
{
  "type": "ping"
}

# Server → Client: Frame Update
{
  "type": "frame",
  "frame_id": 1250,
  "timestamp": 1701234567.89,
  "detections": {
    "person_count": 2,
    "river_detected": true,
    "max_overlap_ratio": 0.45
  }
}

# Server → Client: Alert
{
  "type": "alert",
  "severity": "warning",
  "message": "Drowning danger detected!",
  "incident_id": "uuid",
  "overlap_ratio": 0.95,
  "camera_id": "demo.mp4",
  "timestamp": 1701234567.89
}

# Server → Client: Status Update
{
  "type": "status",
  "status": "running" | "stopped" | "error",
  "message": "Processing frame 1250/5000"
}

# Server → Client: Error
{
  "type": "error",
  "error": "Video file not found",
  "details": "..."
}
```

### 2. Backend Service Layer

#### 2.1 DetectionService

```python
class DetectionService:
    """Manages video detection sessions"""
    
    def __init__(self):
        self.current_session: Optional[DetectionSession] = None
        self.session_lock = threading.Lock()
    
    async def start_detection(
        self, 
        video_source: Union[str, int],
        is_webcam: bool = False
    ) -> str:
        """Start a new detection session"""
        pass
    
    async def stop_detection(self) -> Dict[str, Any]:
        """Stop current detection session"""
        pass
    
    def get_status(self) -> Dict[str, Any]:
        """Get current detection status"""
        pass
```

#### 2.2 WebSocketManager

```python
class WebSocketManager:
    """Manages WebSocket connections and broadcasts"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        """Accept new WebSocket connection"""
        pass
    
    async def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection"""
        pass
    
    async def broadcast(self, message: dict):
        """Send message to all connected clients"""
        pass
    
    async def send_frame_update(self, frame_data: dict):
        """Broadcast frame update"""
        pass
    
    async def send_alert(self, alert_data: dict):
        """Broadcast alert"""
        pass
```

#### 2.3 DetectionSession

```python
@dataclass
class DetectionSession:
    """Represents an active detection session"""
    session_id: str
    video_source: Union[str, int]
    is_webcam: bool
    start_time: float
    processor: VideoProcessor
    thread: threading.Thread
    status: str  # "running", "stopping", "stopped"
    statistics: Dict[str, Any]
```

### 3. Frontend Components

#### 3.1 Main Window Structure

```
App
├── NavigationBar
│   ├── Logo
│   ├── MenuItem: Real-time Detection
│   ├── MenuItem: Incident History
│   ├── MenuItem: Settings
│   └── MenuItem: Logs
│
├── DetectionPage
│   ├── VideoSourceSelector
│   │   ├── FileInput
│   │   └── WebcamSelector
│   ├── ControlPanel
│   │   ├── StartButton
│   │   ├── StopButton
│   │   └── StatusIndicator
│   ├── VideoDisplay
│   │   ├── Canvas (for video frames)
│   │   └── OverlayInfo (FPS, frame count)
│   └── AlertPanel
│       └── AlertList (recent alerts)
│
├── IncidentPage
│   ├── FilterBar
│   │   ├── DateRangePicker
│   │   └── SearchInput
│   ├── IncidentGrid
│   │   └── IncidentCard[]
│   │       ├── Thumbnail
│   │       ├── Timestamp
│   │       ├── OverlapRatio
│   │       └── Actions (View, Delete)
│   └── IncidentDetailModal
│       ├── Screenshot
│       ├── Metadata
│       └── VLMDescription
│
├── SettingsPage
│   ├── EmailSettings
│   ├── VLMSettings
│   ├── LoggingSettings
│   └── SaveButton
│
└── LogsPage
    ├── LogLevelFilter
    └── LogViewer
```

#### 3.2 React Component Examples

```typescript
// DetectionPage.tsx
interface DetectionPageProps {}

const DetectionPage: React.FC<DetectionPageProps> = () => {
  const [status, setStatus] = useState<'idle' | 'running' | 'stopping'>('idle');
  const [videoSource, setVideoSource] = useState<string>('');
  const [ws, setWs] = useState<WebSocket | null>(null);
  
  const handleStart = async () => {
    const response = await fetch('http://127.0.0.1:8001/api/detection/start', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ video_source: videoSource })
    });
    
    if (response.ok) {
      connectWebSocket();
      setStatus('running');
    }
  };
  
  const connectWebSocket = () => {
    const websocket = new WebSocket('ws://127.0.0.1:8001/ws');
    
    websocket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      if (data.type === 'frame') {
        updateVideoFrame(data);
      } else if (data.type === 'alert') {
        showAlert(data);
      }
    };
    
    setWs(websocket);
  };
  
  return (
    <div className="detection-page">
      <VideoSourceSelector onChange={setVideoSource} />
      <ControlPanel 
        status={status}
        onStart={handleStart}
        onStop={handleStop}
      />
      <VideoDisplay />
      <AlertPanel />
    </div>
  );
};
```

### 4. Electron Main Process

```javascript
// main.js
const { app, BrowserWindow, dialog } = require('electron');
const { spawn } = require('child_process');
const path = require('path');
const axios = require('axios');

let mainWindow = null;
let pythonProcess = null;
const BACKEND_PORT = 8001;
const BACKEND_URL = `http://127.0.0.1:${BACKEND_PORT}`;

// Start Python backend
function startBackend() {
  const pythonExecutable = process.env.PYTHON_PATH || 'python';
  const backendScript = path.join(__dirname, '../backend/api.py');
  
  pythonProcess = spawn(pythonExecutable, [backendScript]);
  
  pythonProcess.stdout.on('data', (data) => {
    console.log(`[Backend] ${data}`);
  });
  
  pythonProcess.stderr.on('data', (data) => {
    console.error(`[Backend Error] ${data}`);
  });
  
  pythonProcess.on('close', (code) => {
    console.log(`Backend process exited with code ${code}`);
  });
}

// Check if backend is running
async function checkBackend(maxRetries = 30) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      await axios.get(`${BACKEND_URL}/health`);
      return true;
    } catch (error) {
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
  }
  return false;
}

app.on('ready', async () => {
  // Start backend
  startBackend();
  
  // Wait for backend to be ready
  const backendReady = await checkBackend();
  
  if (!backendReady) {
    dialog.showErrorBox(
      '启动失败',
      '无法启动后端服务。请确保已安装 Python 和所有依赖。'
    );
    app.quit();
    return;
  }
  
  // Create main window
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false
    },
    icon: path.join(__dirname, 'assets/icon.png')
  });
  
  // Load frontend
  if (process.env.NODE_ENV === 'development') {
    mainWindow.loadURL('http://localhost:3000');
    mainWindow.webContents.openDevTools();
  } else {
    mainWindow.loadFile('build/index.html');
  }
});

app.on('quit', () => {
  // Kill backend process
  if (pythonProcess) {
    pythonProcess.kill();
  }
});
```

## Data Models

### Backend Models

```python
# models.py
from pydantic import BaseModel, Field
from typing import Optional, List, Union
from datetime import datetime

class DetectionStartRequest(BaseModel):
    video_source: Union[str, int]
    is_webcam: bool = False

class DetectionStartResponse(BaseModel):
    session_id: str
    status: str
    message: str

class DetectionStatusResponse(BaseModel):
    status: str
    session_id: Optional[str]
    current_frame: int
    fps: float
    elapsed_time: float
    video_source: Optional[str]

class IncidentResponse(BaseModel):
    incident_id: str
    camera_id: str
    frame_id: int
    timestamp: float
    overlap_ratio: float
    bbox: List[int]
    screenshot_url: str
    vlm_summary: Optional[str]
    vlm_confidence: Optional[float]
    status: str

class ConfigUpdateRequest(BaseModel):
    email: Optional[dict]
    vlm: Optional[dict]
    logging: Optional[dict]

class WebSocketMessage(BaseModel):
    type: str
    data: dict
```



## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*


### Property Reflection

After reviewing the prework analysis, several properties can be consolidated:

- Many frontend UI tests (6.x, 7.x, 8.x, 9.x, 10.x) are integration tests that verify UI behavior, but are better tested manually or with E2E tests rather than property-based tests
- Backend API properties (2.x, 4.x, 5.x) can be consolidated into general API contract properties
- WebSocket properties (3.x) focus on message delivery and error handling
- The core testable properties focus on: API contracts, concurrency control, data persistence, error handling

Consolidated properties focus on:
1. API endpoint contracts and response formats
2. Session management and concurrency
3. WebSocket message delivery
4. Data persistence and filtering
5. Configuration validation and security

### Correctness Properties

Property 1: API start detection returns session ID
*For any* valid video source provided to POST /api/detection/start, the response should contain a valid session_id and status "started"
**Validates: Requirements 2.1**

Property 2: Single session concurrency
*For any* backend state where a detection session is running, attempting to start another session should return an error status
**Validates: Requirements 1.3, 2.5**

Property 3: Background task non-blocking
*For any* detection start request, the API response should return within 2 seconds while video processing continues in background
**Validates: Requirements 1.2**

Property 4: Status endpoint completeness
*For any* GET request to /api/detection/status, the response should contain all required fields: status, current_frame, fps, elapsed_time
**Validates: Requirements 2.3**

Property 5: WebSocket frame broadcast
*For any* video frame processed during detection, all connected WebSocket clients should receive a frame update message
**Validates: Requirements 3.2**

Property 6: WebSocket alert propagation
*For any* drowning danger detection event, all connected WebSocket clients should receive an alert message within 1 second
**Validates: Requirements 3.3**

Property 7: WebSocket disconnection resilience
*For any* WebSocket client disconnection during active detection, the detection process should continue without interruption
**Validates: Requirements 3.4**

Property 8: Incident list pagination
*For any* valid page and limit parameters, GET /api/incidents should return exactly min(limit, remaining_incidents) items
**Validates: Requirements 4.3**

Property 9: Incident date filtering
*For any* date range filter applied to /api/incidents, all returned incidents should have timestamps within the specified range
**Validates: Requirements 4.4**

Property 10: Incident deletion completeness
*For any* valid incident ID, DELETE /api/incidents/{id} should remove both the database record and associated screenshot file
**Validates: Requirements 4.5**

Property 11: Configuration update persistence
*For any* valid configuration update via PUT /api/config, reading the configuration file should reflect the new values
**Validates: Requirements 5.4**

Property 12: Configuration validation
*For any* invalid configuration data sent to PUT /api/config, the response should contain validation errors with field-specific messages
**Validates: Requirements 5.3**

Property 13: Sensitive data masking
*For any* GET request to /api/config, sensitive fields (api_key, password) should be masked or partially hidden
**Validates: Requirements 5.5**

Property 14: Resource cleanup on session end
*For any* detection session that completes or is stopped, all associated resources (threads, file handles, memory) should be released
**Validates: Requirements 1.5**

## Error Handling

### Backend API Errors

**Scenario**: Invalid video source provided

**Handling**:
```python
try:
    processor = VideoProcessor(video_source, ...)
except FileNotFoundError:
    raise HTTPException(
        status_code=400,
        detail="Video file not found"
    )
except Exception as e:
    raise HTTPException(
        status_code=500,
        detail=f"Failed to start detection: {str(e)}"
    )
```

**Scenario**: Detection already running

**Handling**:
```python
if detection_service.current_session:
    raise HTTPException(
        status_code=409,
        detail="Detection session already in progress"
    )
```

**Scenario**: WebSocket connection error

**Handling**:
```python
try:
    await websocket.send_json(message)
except WebSocketDisconnect:
    await ws_manager.disconnect(websocket)
except Exception as e:
    logger.error(f"WebSocket error: {e}")
    # Continue with other clients
```

### Frontend Error Handling

**Scenario**: Backend connection failed

**Handling**:
```typescript
try {
  const response = await fetch(`${BACKEND_URL}/health`);
  if (!response.ok) throw new Error('Backend not responding');
} catch (error) {
  showError('无法连接到后端服务。请确保后端正在运行。');
  setConnectionStatus('disconnected');
  // Show retry button
}
```

**Scenario**: WebSocket disconnection

**Handling**:
```typescript
websocket.onclose = () => {
  console.log('WebSocket disconnected, attempting reconnect...');
  setTimeout(() => {
    connectWebSocket();
  }, 3000);
};
```

**Scenario**: API request timeout

**Handling**:
```typescript
const controller = new AbortController();
const timeoutId = setTimeout(() => controller.abort(), 10000);

try {
  const response = await fetch(url, {
    signal: controller.signal
  });
} catch (error) {
  if (error.name === 'AbortError') {
    showError('请求超时，请重试');
  }
} finally {
  clearTimeout(timeoutId);
}
```

## Testing Strategy

### Backend Unit Testing

使用 pytest 和 pytest-asyncio 进行后端测试：

1. **API Endpoint Tests**
   - 测试所有 REST endpoints 的请求/响应
   - 测试参数验证
   - 测试错误处理

2. **Service Layer Tests**
   - 测试 DetectionService 会话管理
   - 测试 WebSocketManager 消息广播
   - 测试 IncidentService CRUD 操作

3. **Integration Tests**
   - 测试完整的检测流程
   - 测试 WebSocket 通信
   - 测试配置更新流程

### Frontend Unit Testing

使用 Jest 和 React Testing Library：

1. **Component Tests**
   - 测试组件渲染
   - 测试用户交互
   - 测试状态管理

2. **API Client Tests**
   - 测试 API 调用逻辑
   - 测试错误处理
   - 测试重试机制

3. **WebSocket Tests**
   - 测试连接管理
   - 测试消息处理
   - 测试重连逻辑

### Property-Based Testing

使用 Hypothesis (Python) 进行属性测试：

**测试框架**: Hypothesis
**最小迭代次数**: 100

1. **Property 1: API session ID validity**
   - 生成随机视频源
   - 验证返回的 session_id 格式正确

2. **Property 5: WebSocket broadcast**
   - 生成随机数量的 WebSocket 连接
   - 验证所有连接都收到消息

3. **Property 8: Pagination correctness**
   - 生成随机 page/limit 参数
   - 验证返回的项目数量正确

4. **Property 9: Date filtering**
   - 生成随机日期范围
   - 验证所有返回的事件在范围内

5. **Property 13: Sensitive data masking**
   - 生成随机配置数据
   - 验证敏感字段被正确掩码

### End-to-End Testing

使用 Playwright 进行 E2E 测试：

1. **Complete Detection Flow**
   - 启动应用
   - 选择视频源
   - 开始检测
   - 验证实时显示
   - 停止检测
   - 验证统计信息

2. **Incident Management Flow**
   - 查看事件列表
   - 应用过滤器
   - 查看事件详情
   - 删除事件

3. **Configuration Flow**
   - 修改配置
   - 保存配置
   - 验证配置生效

## Implementation Notes

### 后端实现要点

1. **异步处理**
   - 使用 FastAPI 的后台任务处理视频检测
   - 使用 asyncio 处理 WebSocket 通信
   - 使用线程池处理 CPU 密集型任务

2. **状态管理**
   - 使用单例模式管理 DetectionService
   - 使用线程锁保护共享状态
   - 使用事件通知机制同步状态

3. **性能优化**
   - 使用 WebSocket 而非轮询减少开销
   - 使用帧率限制避免过载
   - 使用缓存减少重复计算

### 前端实现要点

1. **状态管理**
   - 使用 React Context 或 Redux 管理全局状态
   - 使用 useReducer 管理复杂组件状态
   - 使用 React Query 管理服务器状态

2. **性能优化**
   - 使用 React.memo 避免不必要的重渲染
   - 使用 useMemo/useCallback 优化计算
   - 使用虚拟滚动处理大列表

3. **用户体验**
   - 使用 loading 状态提供反馈
   - 使用 toast 通知显示操作结果
   - 使用防抖/节流优化输入处理

### 打包配置

1. **开发环境**
   ```bash
   # 后端
   cd backend
   uvicorn api:app --reload --port 8001
   
   # 前端
   cd frontend
   npm start
   ```

2. **生产打包**
   ```bash
   # 打包后端 (可选)
   pyinstaller --onefile backend/api.py
   
   # 打包前端
   cd frontend
   npm run build
   electron-builder
   ```

3. **electron-builder 配置**
   ```json
   {
     "build": {
       "appId": "com.drowning.detection",
       "productName": "溺水检测系统",
       "files": [
         "build/**/*",
         "main.js",
         "package.json"
       ],
       "extraResources": [
         {
           "from": "../backend/dist/api.exe",
           "to": "backend.exe"
         },
         {
           "from": "../model",
           "to": "model"
         },
         {
           "from": "../config",
           "to": "config"
         }
       ],
       "win": {
         "target": ["nsis", "portable"],
         "icon": "assets/icon.ico"
       },
       "nsis": {
         "oneClick": false,
         "allowToChangeInstallationDirectory": true,
         "createDesktopShortcut": true
       }
     }
   }
   ```

### 部署选项

**选项 1: 前端独立打包**
- 用户需要先安装 Python 环境
- 用户手动启动后端服务
- 前端 exe 只有 50-100MB

**选项 2: 完整打包**
- 前端 + 后端一起打包
- 用户无需 Python 环境
- 总大小约 900MB-1.5GB

**选项 3: 混合部署**
- 提供两个版本供用户选择
- 开发者版本（需要 Python）
- 完整版本（包含所有依赖）
