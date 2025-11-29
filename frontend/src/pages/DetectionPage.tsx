import React, { useState, useEffect, useRef } from 'react';
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
  CircularProgress,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  ListItemIcon
} from '@mui/material';
import {
  PlayArrow,
  Stop,
  Videocam,
  VideoFile,
  CheckCircle,
  Refresh
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

interface CameraInfo {
  index: number;
  name: string;
  width: number;
  height: number;
  fps: number;
  available: boolean;
}

const DetectionPage: React.FC = () => {
  const [videoSource, setVideoSource] = useState<string>('');
  const [sourceType, setSourceType] = useState<'file' | 'webcam'>('webcam');
  const [selectedCamera, setSelectedCamera] = useState<number>(0);
  const [cameras, setCameras] = useState<CameraInfo[]>([]);
  const [loadingCameras, setLoadingCameras] = useState(false);
  const [previewImage, setPreviewImage] = useState<string | null>(null);
  const [previewActive, setPreviewActive] = useState(false);
  const previewIntervalRef = useRef<NodeJS.Timeout | null>(null);

  const [status, setStatus] = useState<DetectionStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [alerts, setAlerts] = useState<any[]>([]);
  const [currentFrame, setCurrentFrame] = useState<string | null>(null);
  const [frameInfo, setFrameInfo] = useState<any>(null);

  // Load cameras on mount
  useEffect(() => {
    if (sourceType === 'webcam') {
      loadCameras();
    }
  }, [sourceType]);

  // Start preview when camera is selected
  useEffect(() => {
    if (sourceType === 'webcam' && cameras.length > 0 && !status?.status) {
      startCameraPreview(selectedCamera);
    }

    return () => {
      stopCameraPreview();
    };
  }, [selectedCamera, sourceType]);

  // Poll detection status
  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        const statusData = await apiClient.getDetectionStatus();
        setStatus(statusData);
      } catch (err: any) {
        console.error('Failed to get status:', err);
      }
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  // WebSocket handlers
  useEffect(() => {
    const handleFrame = (data: any) => {
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
      }, ...prev].slice(0, 10));
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

  const loadCameras = async () => {
    setLoadingCameras(true);
    try {
      const response = await fetch('http://127.0.0.1:8000/api/camera/list');
      const data = await response.json();
      setCameras(data.cameras || []);
      if (data.cameras && data.cameras.length > 0) {
        setSelectedCamera(data.cameras[0].index);
      }
    } catch (err) {
      console.error('Failed to load cameras:', err);
      setError('Failed to load camera list');
    } finally {
      setLoadingCameras(false);
    }
  };

  const startCameraPreview = async (cameraIndex: number) => {
    // Stop previous preview
    stopCameraPreview();

    try {
      // Start preview on backend
      await fetch(`http://127.0.0.1:8000/api/camera/preview/start/${cameraIndex}`, {
        method: 'POST'
      });

      setPreviewActive(true);

      // Start polling for preview frames
      previewIntervalRef.current = setInterval(async () => {
        try {
          const response = await fetch(`http://127.0.0.1:8000/api/camera/preview/frame/${cameraIndex}`);
          const data = await response.json();
          if (data.image) {
            setPreviewImage(data.image);
          }
        } catch (err) {
          console.error('Failed to get preview frame:', err);
        }
      }, 100); // 10 FPS preview
    } catch (err) {
      console.error('Failed to start preview:', err);
      setError('Failed to start camera preview');
    }
  };

  const stopCameraPreview = async () => {
    if (previewIntervalRef.current) {
      clearInterval(previewIntervalRef.current);
      previewIntervalRef.current = null;
    }

    if (previewActive && selectedCamera !== null) {
      try {
        await fetch(`http://127.0.0.1:8000/api/camera/preview/stop/${selectedCamera}`, {
          method: 'POST'
        });
      } catch (err) {
        console.error('Failed to stop preview:', err);
      }
    }

    setPreviewActive(false);
    setPreviewImage(null);
  };

  const handleStart = async () => {
    setLoading(true);
    setError(null);

    // Stop preview when starting detection
    if (sourceType === 'webcam') {
      stopCameraPreview();
    }

    try {
      const result = await apiClient.startDetection(
        sourceType === 'webcam' ? selectedCamera.toString() : videoSource,
        sourceType === 'webcam'
      );
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

      // Restart preview after stopping detection
      if (sourceType === 'webcam') {
        setTimeout(() => {
          startCameraPreview(selectedCamera);
        }, 500);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || '停止检测失败');
    } finally {
      setLoading(false);
    }
  };

  const isRunning = status?.status === 'running';
  const canStart = !isRunning && (sourceType === 'webcam' || videoSource.trim() !== '');
  const displayImage = isRunning ? currentFrame : (sourceType === 'webcam' ? previewImage : null);

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Real-time Detection
      </Typography>

      {error && (
        <Alert severity="error" onClose={() => setError(null)} sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* Control Panel */}
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Video Source Configuration
            </Typography>

            <FormControl fullWidth sx={{ mb: 2 }}>
              <InputLabel>Source Type</InputLabel>
              <Select
                value={sourceType}
                label="Source Type"
                onChange={(e) => setSourceType(e.target.value as 'file' | 'webcam')}
                disabled={isRunning}
              >
                <MenuItem value="file">
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <VideoFile sx={{ mr: 1 }} />
                    Video File
                  </Box>
                </MenuItem>
                <MenuItem value="webcam">
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <Videocam sx={{ mr: 1 }} />
                    Webcam
                  </Box>
                </MenuItem>
              </Select>
            </FormControl>

            {sourceType === 'file' ? (
              <TextField
                fullWidth
                label="Video File Path"
                value={videoSource}
                onChange={(e) => setVideoSource(e.target.value)}
                placeholder="e.g., D:/videos/sample.mp4"
                disabled={isRunning}
                sx={{ mb: 2 }}
              />
            ) : (
              <Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                  <Typography variant="subtitle2">Available Cameras</Typography>
                  <Button
                    size="small"
                    onClick={loadCameras}
                    disabled={loadingCameras || isRunning}
                    startIcon={<Refresh />}
                  >
                    Refresh
                  </Button>
                </Box>

                {loadingCameras ? (
                  <Box sx={{ display: 'flex', justifyContent: 'center', p: 2 }}>
                    <CircularProgress size={24} />
                  </Box>
                ) : cameras.length > 0 ? (
                  <List dense sx={{ bgcolor: 'background.paper', borderRadius: 1, mb: 2 }}>
                    {cameras.map((camera) => (
                      <ListItem key={camera.index} disablePadding>
                        <ListItemButton
                          selected={selectedCamera === camera.index}
                          onClick={() => setSelectedCamera(camera.index)}
                          disabled={isRunning}
                        >
                          <ListItemIcon>
                            {selectedCamera === camera.index && <CheckCircle color="primary" />}
                          </ListItemIcon>
                          <ListItemText
                            primary={camera.name}
                            secondary={`${camera.width}x${camera.height} @ ${camera.fps}fps`}
                          />
                        </ListItemButton>
                      </ListItem>
                    ))}
                  </List>
                ) : (
                  <Alert severity="warning" sx={{ mb: 2 }}>
                    No cameras found. Click Refresh to scan again.
                  </Alert>
                )}
              </Box>
            )}

            <Box sx={{ display: 'flex', gap: 2 }}>
              <Button
                variant="contained"
                color="primary"
                fullWidth
                startIcon={<PlayArrow />}
                onClick={handleStart}
                disabled={!canStart || loading}
              >
                {loading ? <CircularProgress size={24} /> : 'Start Detection'}
              </Button>

              <Button
                variant="outlined"
                color="error"
                fullWidth
                startIcon={<Stop />}
                onClick={handleStop}
                disabled={!isRunning || loading}
              >
                Stop
              </Button>
            </Box>
          </Paper>

          {/* Status Card */}
          <Paper sx={{ p: 3, mt: 3 }}>
            <Typography variant="h6" gutterBottom>
              Detection Status
            </Typography>

            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                <Typography variant="body2" color="text.secondary">Status:</Typography>
                <Chip
                  label={status?.status || 'idle'}
                  color={isRunning ? 'success' : 'default'}
                  size="small"
                />
              </Box>

              <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                <Typography variant="body2" color="text.secondary">Frame:</Typography>
                <Typography variant="body2">{status?.current_frame || 0}</Typography>
              </Box>

              <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                <Typography variant="body2" color="text.secondary">FPS:</Typography>
                <Typography variant="body2">{status?.fps?.toFixed(2) || '0.00'}</Typography>
              </Box>

              <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                <Typography variant="body2" color="text.secondary">Runtime:</Typography>
                <Typography variant="body2">{status?.elapsed_time?.toFixed(1) || '0.0'}s</Typography>
              </Box>
            </Box>
          </Paper>
        </Grid>

        {/* Video Display */}
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              {isRunning ? 'Detection Feed' : 'Camera Preview'}
            </Typography>

            <Box
              sx={{
                bgcolor: 'black',
                borderRadius: 1,
                overflow: 'hidden',
                position: 'relative',
                minHeight: 400,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}
            >
              {displayImage ? (
                <img
                  src={displayImage}
                  alt={isRunning ? "Detection Feed" : "Camera Preview"}
                  style={{ width: '100%', height: 'auto', display: 'block' }}
                />
              ) : (
                <Typography variant="body2" color="text.secondary">
                  {sourceType === 'webcam'
                    ? 'Select a camera to start preview'
                    : 'Start detection to see video'}
                </Typography>
              )}

              {/* Detection Info Overlay */}
              {isRunning && frameInfo && (
                <Box
                  sx={{
                    position: 'absolute',
                    top: 10,
                    left: 10,
                    bgcolor: 'rgba(0, 0, 0, 0.7)',
                    color: 'white',
                    padding: 1,
                    borderRadius: 1
                  }}
                >
                  <Typography variant="caption" display="block">
                    Frame: {frameInfo.frame_id}
                  </Typography>
                  {frameInfo.detections?.warning_active && (
                    <Typography variant="caption" display="block" color="error">
                      ⚠ WARNING: Drowning Detected!
                    </Typography>
                  )}
                </Box>
              )}
            </Box>

            {/* Detection Info */}
            {isRunning && frameInfo?.detections && (
              <Grid container spacing={2} sx={{ mt: 2 }}>
                <Grid item xs={4}>
                  <Card variant="outlined">
                    <CardContent>
                      <Typography variant="caption" color="text.secondary">
                        Person Detected
                      </Typography>
                      <Typography variant="h6">
                        {frameInfo.detections.person_detected ? 'Yes' : 'No'}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={4}>
                  <Card variant="outlined">
                    <CardContent>
                      <Typography variant="caption" color="text.secondary">
                        Overlap Ratio
                      </Typography>
                      <Typography variant="h6">
                        {(frameInfo.detections.overlap_ratio * 100).toFixed(1)}%
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={4}>
                  <Card variant="outlined">
                    <CardContent>
                      <Typography variant="caption" color="text.secondary">
                        Alert Status
                      </Typography>
                      <Typography variant="h6" color={frameInfo.detections.warning_active ? 'error' : 'success'}>
                        {frameInfo.detections.warning_active ? 'ALERT' : 'Normal'}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
              </Grid>
            )}
          </Paper>

          {/* Recent Alerts */}
          {alerts.length > 0 && (
            <Paper sx={{ p: 3, mt: 3 }}>
              <Typography variant="h6" gutterBottom>
                Recent Alerts
              </Typography>
              <List dense>
                {alerts.map((alert) => (
                  <ListItem key={alert.id}>
                    <Alert severity="warning" sx={{ width: '100%' }}>
                      {alert.message} - {new Date(alert.timestamp * 1000).toLocaleTimeString()}
                    </Alert>
                  </ListItem>
                ))}
              </List>
            </Paper>
          )}
        </Grid>
      </Grid>
    </Box>
  );
};

export default DetectionPage;
