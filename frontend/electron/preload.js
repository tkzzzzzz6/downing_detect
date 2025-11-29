// Preload script for Electron
// This script runs before the renderer process loads
// It can be used to expose limited APIs to the renderer

const { contextBridge } = require('electron');

// Expose protected methods that allow the renderer process to use
// specific functionality from the main process
contextBridge.exposeInMainWorld('electron', {
  // Add any electron APIs you want to expose to the renderer
  versions: {
    node: process.versions.node,
    chrome: process.versions.chrome,
    electron: process.versions.electron
  }
});
