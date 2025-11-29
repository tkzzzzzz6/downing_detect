import React, { useState, useEffect } from 'react';
import {
  BrowserRouter as Router,
  Routes,
  Route,
  Link,
  Navigate
} from 'react-router-dom';
import {
  ThemeProvider,
  createTheme,
  CssBaseline,
  AppBar,
  Toolbar,
  Typography,
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Box,
  Alert,
  Snackbar
} from '@mui/material';
import {
  Videocam,
  History,
  Settings,
  Description
} from '@mui/icons-material';

import DetectionPage from './pages/DetectionPage';
import IncidentPage from './pages/IncidentPage';
import SettingsPage from './pages/SettingsPage';
import apiClient from './services/api';

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
});

const drawerWidth = 240;

const App: React.FC = () => {
  const [backendStatus, setBackendStatus] = useState<'checking' | 'connected' | 'error'>('checking');
  const [snackbar, setSnackbar] = useState<{ open: boolean; message: string; severity: 'success' | 'error' | 'info' }>({
    open: false,
    message: '',
    severity: 'info'
  });

  useEffect(() => {
    // Check backend connection
    const checkBackend = async () => {
      try {
        await apiClient.healthCheck();
        setBackendStatus('connected');
        showSnackbar('后端服务连接成功', 'success');
      } catch (error) {
        setBackendStatus('error');
        showSnackbar('无法连接到后端服务', 'error');
        // Retry after 3 seconds
        setTimeout(checkBackend, 3000);
      }
    };

    checkBackend();
  }, []);

  const showSnackbar = (message: string, severity: 'success' | 'error' | 'info') => {
    setSnackbar({ open: true, message, severity });
  };

  const handleCloseSnackbar = () => {
    setSnackbar({ ...snackbar, open: false });
  };

  const menuItems = [
    { text: '实时检测', icon: <Videocam />, path: '/detection' },
    { text: '事件历史', icon: <History />, path: '/incidents' },
    { text: '系统设置', icon: <Settings />, path: '/settings' },
  ];

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <Box sx={{ display: 'flex' }}>
          {/* App Bar */}
          <AppBar
            position="fixed"
            sx={{ zIndex: (theme) => theme.zIndex.drawer + 1 }}
          >
            <Toolbar>
              <Typography variant="h6" noWrap component="div">
                溺水检测系统
              </Typography>
              <Box sx={{ flexGrow: 1 }} />
              <Box
                sx={{
                  width: 12,
                  height: 12,
                  borderRadius: '50%',
                  bgcolor: backendStatus === 'connected' ? 'success.main' : 'error.main',
                  mr: 1
                }}
              />
              <Typography variant="body2">
                {backendStatus === 'connected' ? '已连接' : backendStatus === 'checking' ? '连接中...' : '连接失败'}
              </Typography>
            </Toolbar>
          </AppBar>

          {/* Side Drawer */}
          <Drawer
            variant="permanent"
            sx={{
              width: drawerWidth,
              flexShrink: 0,
              [`& .MuiDrawer-paper`]: { width: drawerWidth, boxSizing: 'border-box' },
            }}
          >
            <Toolbar />
            <Box sx={{ overflow: 'auto' }}>
              <List>
                {menuItems.map((item) => (
                  <ListItem key={item.text} disablePadding>
                    <ListItemButton component={Link} to={item.path}>
                      <ListItemIcon>
                        {item.icon}
                      </ListItemIcon>
                      <ListItemText primary={item.text} />
                    </ListItemButton>
                  </ListItem>
                ))}
              </List>
            </Box>
          </Drawer>

          {/* Main Content */}
          <Box component="main" sx={{ flexGrow: 1, p: 3 }}>
            <Toolbar />
            {backendStatus === 'error' && (
              <Alert severity="error" sx={{ mb: 2 }}>
                无法连接到后端服务。请确保后端正在运行并检查网络连接。
              </Alert>
            )}
            <Routes>
              <Route path="/" element={<Navigate to="/detection" replace />} />
              <Route path="/detection" element={<DetectionPage />} />
              <Route path="/incidents" element={<IncidentPage />} />
              <Route path="/settings" element={<SettingsPage />} />
            </Routes>
          </Box>
        </Box>

        {/* Snackbar for notifications */}
        <Snackbar
          open={snackbar.open}
          autoHideDuration={6000}
          onClose={handleCloseSnackbar}
          anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
        >
          <Alert onClose={handleCloseSnackbar} severity={snackbar.severity} sx={{ width: '100%' }}>
            {snackbar.message}
          </Alert>
        </Snackbar>
      </Router>
    </ThemeProvider>
  );
};

export default App;
