const { app, BrowserWindow, dialog } = require('electron');
const { spawn } = require('child_process');
const path = require('path');
const axios = require('axios');

let mainWindow = null;
let pythonProcess = null;
const BACKEND_PORT = 8001;
const BACKEND_URL = `http://127.0.0.1:${BACKEND_PORT}`;

/**
 * Start Python backend process
 */
function startBackend() {
  // Try to find python executable
  const pythonExecutable = process.env.PYTHON_PATH || 'python';
  const backendScript = path.join(__dirname, '../../backend/api.py');

  console.log(`Starting backend: ${pythonExecutable} ${backendScript}`);

  pythonProcess = spawn(pythonExecutable, [backendScript], {
    cwd: path.join(__dirname, '../../')
  });

  pythonProcess.stdout.on('data', (data) => {
    console.log(`[Backend] ${data}`);
  });

  pythonProcess.stderr.on('data', (data) => {
    console.error(`[Backend Error] ${data}`);
  });

  pythonProcess.on('close', (code) => {
    console.log(`Backend process exited with code ${code}`);
  });

  pythonProcess.on('error', (err) => {
    console.error(`Failed to start backend: ${err.message}`);
  });
}

/**
 * Check if backend is running
 */
async function checkBackend(maxRetries = 30) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      await axios.get(`${BACKEND_URL}/health`);
      console.log('Backend is ready!');
      return true;
    } catch (error) {
      console.log(`Waiting for backend... (${i + 1}/${maxRetries})`);
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
  }
  return false;
}

/**
 * Create main window
 */
function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js')
    },
    icon: path.join(__dirname, '../public/icon.png')
  });

  // Load frontend
  if (process.env.NODE_ENV === 'development') {
    mainWindow.loadURL('http://localhost:3000');
    mainWindow.webContents.openDevTools();
  } else {
    mainWindow.loadFile(path.join(__dirname, '../build/index.html'));
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

/**
 * App ready event
 */
app.on('ready', async () => {
  // Start backend
  startBackend();

  // Wait for backend to be ready
  const backendReady = await checkBackend();

  if (!backendReady) {
    dialog.showErrorBox(
      '启动失败',
      '无法启动后端服务。请确保已安装 Python 和所有依赖。\n\n' +
      '请运行以下命令安装依赖:\n' +
      'cd backend\n' +
      'pip install -r requirements.txt'
    );
    app.quit();
    return;
  }

  // Create main window
  createWindow();
});

/**
 * App quit event
 */
app.on('quit', () => {
  // Kill backend process
  if (pythonProcess) {
    pythonProcess.kill();
    console.log('Backend process terminated');
  }
});

/**
 * macOS specific: re-create window when dock icon is clicked
 */
app.on('activate', () => {
  if (mainWindow === null) {
    createWindow();
  }
});

/**
 * Close all windows
 */
app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});
