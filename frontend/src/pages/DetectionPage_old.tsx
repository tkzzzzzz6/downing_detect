import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Card,
  CardContent,
  Grid,
  Chip,
  Alert,
  CircularProgress
} from '@mui/material';
import {
  PlayArrow,
  Stop,
  Videocam,
  VideoFile
} from '@mui/icons-material';
import apiClient from '../services/api';

interface DetectionStatus {
  status: string;
  session_id: string | null;
  current_frame: number;
  fps: number;
  elapsed_time: number;
  video_source: string | null;
}

const DetectionPage: React.FC = () => {
  const [videoSource, setVideoSource] = useState<string>('');
  const [sourceType, setSourceType] = useState<'file' | 'webcam'>('file');
  const [cameraIndex, setCameraIndex] = useState<number>(0);
  const [status, setStatus] = useState<DetectionStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [alerts, setAlerts] = useState<any[]>([]);
  const [currentFrame, setCurrentFrame] = useState<string | null>(null);
  const [frameInfo, setFrameInfo] = useState<any>(null);

  useEffect(() => {
    // Poll status periodically
    const interval = setInterval(async () => {
      try {
        const statusData = await apiClient.getDetectionStatus();
        setStatus(statusData);
      } catch (err) {
        console.error('Failed to get status:', err);
      }
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    // Connect to WebSocket for real-time updates
    apiClient.connectWebSocket();

    const handleFrame = (data: any) => {
      // Update current frame
      if (data.image) {
        setCurrentFrame(data.image);
        setFrameInfo({
          frame_id: data.frame_id,
          detections: data.detections
        });
      }
    };

    const handleAlert = (data: any) => {
      console.log('Alert received:', data);
      setAlerts(prev => [{
        ...data,
        id: Date.now()
      }, ...prev].slice(0, 10)); // Keep last 10 alerts
    };

    const handleStatus = (data: any) => {
      console.log('Status update:', data);
    };

    const handleError = (data: any) => {
      setError(data.error);
    };

    apiClient.onWebSocketMessage('frame', handleFrame);
    apiClient.onWebSocketMessage('alert', handleAlert);
    apiClient.onWebSocketMessage('status', handleStatus);
    apiClient.onWebSocketMessage('error', handleError);

    return () => {
      apiClient.offWebSocketMessage('frame', handleFrame);
      apiClient.offWebSocketMessage('alert', handleAlert);
      apiClient.offWebSocketMessage('status', handleStatus);
      apiClient.offWebSocketMessage('error', handleError);
    };
  }, []);

  const handleStart = async () => {
    setLoading(true);
    setError(null);
    setCurrentFrame(null);  // Clear previous frame

    try {
      const source = sourceType === 'webcam' ? cameraIndex : videoSource;
      const result = await apiClient.startDetection(source, sourceType === 'webcam');
      console.log('Detection started:', result);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || '启动检测失败');
    } finally {
      setLoading(false);
    }
  };

  const handleStop = async () => {
    setLoading(true);
    setError(null);

    try {
      const result = await apiClient.stopDetection();
      console.log('Detection stopped:', result);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || '停止检测失败');
    } finally {
      setLoading(false);
    }
  };

  const isRunning = status?.status === 'running';
  const canStart = !isRunning && (sourceType === 'webcam' || videoSource.trim() !== '');

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        实时检测
      </Typography>

      {error && (
        <Alert severity="error" onClose={() => setError(null)} sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* Control Panel */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              视频源配置
            </Typography>

            <FormControl fullWidth sx={{ mb: 2 }}>
              <InputLabel>视频源类型</InputLabel>
              <Select
                value={sourceType}
                label="视频源类型"
                onChange={(e) => setSourceType(e.target.value as 'file' | 'webcam')}
                disabled={isRunning}
              >
                <MenuItem value="file">
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <VideoFile sx={{ mr: 1 }} />
                    视频文件
                  </Box>
                </MenuItem>
                <MenuItem value="webcam">
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <Videocam sx={{ mr: 1 }} />
                    摄像头
                  </Box>
                </MenuItem>
              </Select>
            </FormControl>

            {sourceType === 'file' ? (
              <TextField
                fullWidth
                label="视频文件路径"
                value={videoSource}
                onChange={(e) => setVideoSource(e.target.value)}
                disabled={isRunning}
                placeholder="例如: D:\\videos\\test.mp4"
                sx={{ mb: 2 }}
              />
            ) : (
              <FormControl fullWidth sx={{ mb: 2 }}>
                <InputLabel>摄像头索引</InputLabel>
                <Select
                  value={cameraIndex}
                  label="摄像头索引"
                  onChange={(e) => setCameraIndex(Number(e.target.value))}
                  disabled={isRunning}
                >
                  <MenuItem value={0}>摄像头 0</MenuItem>
                  <MenuItem value={1}>摄像头 1</MenuItem>
                  <MenuItem value={2}>摄像头 2</MenuItem>
                </Select>
              </FormControl>
            )}

            <Box sx={{ display: 'flex', gap: 2 }}>
              <Button
                variant="contained"
                color="primary"
                startIcon={loading ? <CircularProgress size={20} /> : <PlayArrow />}
                onClick={handleStart}
                disabled={!canStart || loading}
                fullWidth
              >
                {loading ? '启动中...' : '开始检测'}
              </Button>
              <Button
                variant="contained"
                color="error"
                startIcon={<Stop />}
                onClick={handleStop}
                disabled={!isRunning || loading}
                fullWidth
              >
                停止检测
              </Button>
            </Box>
          </Paper>
        </Grid>

        {/* Status Display */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              检测状态
            </Typography>

            <Box sx={{ mb: 2 }}>
              <Chip
                label={status?.status === 'running' ? '运行中' : status?.status === 'stopping' ? '停止中' : '空闲'}
                color={status?.status === 'running' ? 'success' : 'default'}
                sx={{ mr: 1 }}
              />
            </Box>

            <Grid container spacing={2}>
              <Grid item xs={6}>
                <Typography variant="body2" color="text.secondary">
                  视频源
                </Typography>
                <Typography variant="body1">
                  {status?.video_source || '-'}
                </Typography>
              </Grid>
              <Grid item xs={6}>
                <Typography variant="body2" color="text.secondary">
                  当前帧
                </Typography>
                <Typography variant="body1">
                  {status?.current_frame || 0}
                </Typography>
              </Grid>
              <Grid item xs={6}>
                <Typography variant="body2" color="text.secondary">
                  帧率 (FPS)
                </Typography>
                <Typography variant="body1">
                  {status?.fps?.toFixed(2) || '0.00'}
                </Typography>
              </Grid>
              <Grid item xs={6}>
                <Typography variant="body2" color="text.secondary">
                  运行时间
                </Typography>
                <Typography variant="body1">
                  {status?.elapsed_time?.toFixed(1) || '0.0'}s
                </Typography>
              </Grid>
            </Grid>
          </Paper>
        </Grid>

        {/* Video Display */}
        <Grid item xs={12}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              实时视频
            </Typography>

            {currentFrame ? (
              <Box>
                <Box
                  sx={{
                    position: 'relative',
                    width: '100%',
                    maxWidth: 800,
                    margin: '0 auto',
                    backgroundColor: '#000',
                    borderRadius: 1,
                    overflow: 'hidden'
                  }}
                >
                  <img
                    src={currentFrame}
                    alt="Detection Feed"
                    style={{
                      width: '100%',
                      height: 'auto',
                      display: 'block'
                    }}
                  />
                  {frameInfo && (
                    <Box
                      sx={{
                        position: 'absolute',
                        bottom: 8,
                        right: 8,
                        backgroundColor: 'rgba(0, 0, 0, 0.7)',
                        color: 'white',
                        padding: '4px 8px',
                        borderRadius: 1,
                        fontSize: '0.75rem'
                      }}
                    >
                      帧 #{frameInfo.frame_id}
                      {frameInfo.detections?.warning_active && (
                        <span style={{ color: '#ff1744', marginLeft: 8 }}>
                          ⚠️ 危险检测
                        </span>
                      )}
                    </Box>
                  )}
                </Box>
                {frameInfo?.detections && (
                  <Box sx={{ mt: 2 }}>
                    <Grid container spacing={2}>
                      <Grid item xs={4}>
                        <Typography variant="body2" color="text.secondary">
                          人员检测
                        </Typography>
                        <Typography variant="body1">
                          {frameInfo.detections.person_detected ? '是' : '否'}
                        </Typography>
                      </Grid>
                      <Grid item xs={4}>
                        <Typography variant="body2" color="text.secondary">
                          重叠率
                        </Typography>
                        <Typography variant="body1" color={frameInfo.detections.overlap_ratio > 0.9 ? 'error' : 'inherit'}>
                          {(frameInfo.detections.overlap_ratio * 100).toFixed(2)}%
                        </Typography>
                      </Grid>
                      <Grid item xs={4}>
                        <Typography variant="body2" color="text.secondary">
                          告警状态
                        </Typography>
                        <Chip
                          label={frameInfo.detections.warning_active ? '告警中' : '正常'}
                          color={frameInfo.detections.warning_active ? 'error' : 'success'}
                          size="small"
                        />
                      </Grid>
                    </Grid>
                  </Box>
                )}
              </Box>
            ) : (
              <Box
                sx={{
                  width: '100%',
                  maxWidth: 800,
                  height: 400,
                  margin: '0 auto',
                  backgroundColor: '#f5f5f5',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  borderRadius: 1
                }}
              >
                <Typography color="text.secondary">
                  {isRunning ? '等待视频帧...' : '未运行检测'}
                </Typography>
              </Box>
            )}
          </Paper>
        </Grid>

        {/* Alerts Panel */}
        <Grid item xs={12}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              实时告警
            </Typography>

            {alerts.length === 0 ? (
              <Typography color="text.secondary">
                暂无告警
              </Typography>
            ) : (
              <Box sx={{ maxHeight: 400, overflow: 'auto' }}>
                {alerts.map((alert) => (
                  <Alert
                    key={alert.id}
                    severity="warning"
                    sx={{ mb: 1 }}
                  >
                    <Typography variant="body1">
                      {alert.message}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      相机: {alert.camera_id} | 重叠率: {(alert.overlap_ratio * 100).toFixed(1)}% |
                      时间: {new Date(alert.timestamp * 1000).toLocaleString()}
                    </Typography>
                  </Alert>
                ))}
              </Box>
            )}
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default DetectionPage;
