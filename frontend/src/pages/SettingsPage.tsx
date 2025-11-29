import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Grid,
  Divider,
  Alert,
  FormControlLabel,
  Switch,
  Select,
  MenuItem,
  FormControl,
  InputLabel
} from '@mui/material';
import { Save } from '@mui/icons-material';
import apiClient from '../services/api';

const SettingsPage: React.FC = () => {
  const [config, setConfig] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadConfig();
  }, []);

  const loadConfig = async () => {
    try {
      const data = await apiClient.getConfig();
      setConfig(data);
    } catch (err) {
      console.error('Failed to load config:', err);
      setError('加载配置失败');
    }
  };

  const handleSave = async () => {
    setLoading(true);
    setSuccess(false);
    setError(null);

    try {
      await apiClient.updateConfig(config);
      setSuccess(true);
      setTimeout(() => setSuccess(false), 3000);
    } catch (err: any) {
      setError(err.response?.data?.detail || '保存配置失败');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (section: string, field: string, value: any) => {
    setConfig((prev: any) => ({
      ...prev,
      [section]: {
        ...prev[section],
        [field]: value
      }
    }));
  };

  if (!config) {
    return <Typography>加载中...</Typography>;
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        系统设置
      </Typography>

      {success && (
        <Alert severity="success" sx={{ mb: 2 }}>
          配置已保存成功！部分配置可能需要重启后端才能生效。
        </Alert>
      )}

      {error && (
        <Alert severity="error" onClose={() => setError(null)} sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          邮件配置
        </Typography>
        <Divider sx={{ mb: 2 }} />

        <Grid container spacing={2}>
          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              label="SMTP 服务器"
              value={config.email.smtp_server}
              onChange={(e) => handleChange('email', 'smtp_server', e.target.value)}
            />
          </Grid>
          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              label="SMTP 端口"
              type="number"
              value={config.email.smtp_port}
              onChange={(e) => handleChange('email', 'smtp_port', parseInt(e.target.value))}
            />
          </Grid>
          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              label="用户名"
              value={config.email.username}
              onChange={(e) => handleChange('email', 'username', e.target.value)}
            />
          </Grid>
          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              label="密码"
              type="password"
              value={config.email.password}
              onChange={(e) => handleChange('email', 'password', e.target.value)}
              placeholder="保密信息，显示为 ***"
            />
          </Grid>
          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              label="发件人邮箱"
              value={config.email.sender}
              onChange={(e) => handleChange('email', 'sender', e.target.value)}
            />
          </Grid>
          <Grid item xs={12} sm={6}>
            <FormControlLabel
              control={
                <Switch
                  checked={config.email.use_tls}
                  onChange={(e) => handleChange('email', 'use_tls', e.target.checked)}
                />
              }
              label="使用 TLS"
            />
          </Grid>
          <Grid item xs={12}>
            <TextField
              fullWidth
              label="收件人列表（逗号分隔）"
              value={config.email.recipients.join(', ')}
              onChange={(e) => handleChange('email', 'recipients', e.target.value.split(',').map((s: string) => s.trim()))}
              helperText="多个收件人请用逗号分隔"
            />
          </Grid>
        </Grid>
      </Paper>

      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          VLM 配置
        </Typography>
        <Divider sx={{ mb: 2 }} />

        <Grid container spacing={2}>
          <Grid item xs={12} sm={6}>
            <FormControl fullWidth>
              <InputLabel>提供商</InputLabel>
              <Select
                value={config.vlm.provider || ''}
                label="提供商"
                onChange={(e) => handleChange('vlm', 'provider', e.target.value)}
              >
                <MenuItem value="openai">OpenAI</MenuItem>
                <MenuItem value="qwen">Qwen (阿里云)</MenuItem>
                <MenuItem value="moonshot">Moonshot</MenuItem>
                <MenuItem value="ollama">Ollama (本地)</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              label="模型名称"
              value={config.vlm.model}
              onChange={(e) => handleChange('vlm', 'model', e.target.value)}
            />
          </Grid>
          <Grid item xs={12}>
            <TextField
              fullWidth
              label="API Key"
              type="password"
              value={config.vlm.api_key || ''}
              onChange={(e) => handleChange('vlm', 'api_key', e.target.value)}
              placeholder="保密信息，显示为 ***"
              helperText="Ollama 本地部署无需填写"
            />
          </Grid>
          <Grid item xs={12}>
            <TextField
              fullWidth
              label="Base URL"
              value={config.vlm.base_url || ''}
              onChange={(e) => handleChange('vlm', 'base_url', e.target.value)}
              helperText="自定义 API 端点（可选）"
            />
          </Grid>
          <Grid item xs={12}>
            <TextField
              fullWidth
              label="提示词模板"
              multiline
              rows={4}
              value={config.vlm.prompt_template}
              onChange={(e) => handleChange('vlm', 'prompt_template', e.target.value)}
            />
          </Grid>
          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              label="超时时间（秒）"
              type="number"
              value={config.vlm.timeout}
              onChange={(e) => handleChange('vlm', 'timeout', parseFloat(e.target.value))}
            />
          </Grid>
          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              label="最大重试次数"
              type="number"
              value={config.vlm.max_retries}
              onChange={(e) => handleChange('vlm', 'max_retries', parseInt(e.target.value))}
            />
          </Grid>
        </Grid>
      </Paper>

      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          日志配置
        </Typography>
        <Divider sx={{ mb: 2 }} />

        <Grid container spacing={2}>
          <Grid item xs={12} sm={6}>
            <FormControl fullWidth>
              <InputLabel>日志级别</InputLabel>
              <Select
                value={config.logging.level}
                label="日志级别"
                onChange={(e) => handleChange('logging', 'level', e.target.value)}
              >
                <MenuItem value="TRACE">TRACE</MenuItem>
                <MenuItem value="DEBUG">DEBUG</MenuItem>
                <MenuItem value="INFO">INFO</MenuItem>
                <MenuItem value="WARNING">WARNING</MenuItem>
                <MenuItem value="ERROR">ERROR</MenuItem>
                <MenuItem value="CRITICAL">CRITICAL</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              label="日志目录"
              value={config.logging.log_dir}
              onChange={(e) => handleChange('logging', 'log_dir', e.target.value)}
            />
          </Grid>
        </Grid>
      </Paper>

      <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
        <Button
          variant="contained"
          color="primary"
          startIcon={<Save />}
          onClick={handleSave}
          disabled={loading}
        >
          {loading ? '保存中...' : '保存配置'}
        </Button>
      </Box>
    </Box>
  );
};

export default SettingsPage;
