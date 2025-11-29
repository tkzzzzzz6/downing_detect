import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Grid,
  Card,
  CardMedia,
  CardContent,
  CardActions,
  Button,
  Pagination,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Chip,
  IconButton
} from '@mui/material';
import { Delete, Visibility } from '@mui/icons-material';
import apiClient from '../services/api';
import { format } from 'date-fns';

interface Incident {
  incident_id: string;
  camera_id: string;
  frame_id: number;
  timestamp: number;
  overlap_ratio: number;
  bbox: number[];
  screenshot_url: string;
  vlm_summary: string | null;
  vlm_confidence: number | null;
  status: string;
}

const IncidentPage: React.FC = () => {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [limit] = useState(12);
  const [loading, setLoading] = useState(false);
  const [selectedIncident, setSelectedIncident] = useState<Incident | null>(null);
  const [detailDialogOpen, setDetailDialogOpen] = useState(false);

  const loadIncidents = async () => {
    setLoading(true);
    try {
      const data = await apiClient.getIncidents(page, limit);
      setIncidents(data.incidents);
      setTotal(data.total);
    } catch (error) {
      console.error('Failed to load incidents:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadIncidents();
  }, [page]);

  const handlePageChange = (event: React.ChangeEvent<unknown>, value: number) => {
    setPage(value);
  };

  const handleViewDetails = async (incident: Incident) => {
    try {
      const fullIncident = await apiClient.getIncident(incident.incident_id);
      setSelectedIncident(fullIncident);
      setDetailDialogOpen(true);
    } catch (error) {
      console.error('Failed to load incident details:', error);
    }
  };

  const handleDelete = async (incidentId: string) => {
    if (window.confirm('确定要删除这条事件记录吗？')) {
      try {
        await apiClient.deleteIncident(incidentId);
        loadIncidents();
      } catch (error) {
        console.error('Failed to delete incident:', error);
        alert('删除失败');
      }
    }
  };

  const totalPages = Math.ceil(total / limit);

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        事件历史
      </Typography>

      <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
        共 {total} 条事件记录
      </Typography>

      {loading ? (
        <Typography>加载中...</Typography>
      ) : incidents.length === 0 ? (
        <Paper sx={{ p: 3, textAlign: 'center' }}>
          <Typography color="text.secondary">
            暂无事件记录
          </Typography>
        </Paper>
      ) : (
        <>
          <Grid container spacing={3}>
            {incidents.map((incident) => (
              <Grid item xs={12} sm={6} md={4} key={incident.incident_id}>
                <Card>
                  <CardMedia
                    component="img"
                    height="200"
                    image={apiClient.getIncidentScreenshotUrl(incident.incident_id)}
                    alt="事件截图"
                  />
                  <CardContent>
                    <Box sx={{ mb: 1 }}>
                      <Chip
                        label={`${(incident.overlap_ratio * 100).toFixed(1)}%`}
                        color="error"
                        size="small"
                        sx={{ mr: 1 }}
                      />
                      <Chip
                        label={incident.status}
                        size="small"
                        color={incident.status === 'notified' ? 'success' : 'default'}
                      />
                    </Box>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      {format(new Date(incident.timestamp * 1000), 'yyyy-MM-dd HH:mm:ss')}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      相机: {incident.camera_id}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      帧号: {incident.frame_id}
                    </Typography>
                    {incident.vlm_summary && (
                      <Typography variant="body2" sx={{ mt: 1 }} noWrap>
                        {incident.vlm_summary}
                      </Typography>
                    )}
                  </CardContent>
                  <CardActions>
                    <Button
                      size="small"
                      startIcon={<Visibility />}
                      onClick={() => handleViewDetails(incident)}
                    >
                      详情
                    </Button>
                    <IconButton
                      size="small"
                      color="error"
                      onClick={() => handleDelete(incident.incident_id)}
                    >
                      <Delete />
                    </IconButton>
                  </CardActions>
                </Card>
              </Grid>
            ))}
          </Grid>

          {totalPages > 1 && (
            <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
              <Pagination
                count={totalPages}
                page={page}
                onChange={handlePageChange}
                color="primary"
              />
            </Box>
          )}
        </>
      )}

      {/* Detail Dialog */}
      <Dialog
        open={detailDialogOpen}
        onClose={() => setDetailDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        {selectedIncident && (
          <>
            <DialogTitle>事件详情</DialogTitle>
            <DialogContent>
              <Box sx={{ textAlign: 'center', mb: 2 }}>
                <img
                  src={apiClient.getIncidentScreenshotUrl(selectedIncident.incident_id)}
                  alt="事件截图"
                  style={{ maxWidth: '100%', height: 'auto' }}
                />
              </Box>

              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <Typography variant="body2" color="text.secondary">
                    事件 ID
                  </Typography>
                  <Typography variant="body1">
                    {selectedIncident.incident_id}
                  </Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2" color="text.secondary">
                    相机 ID
                  </Typography>
                  <Typography variant="body1">
                    {selectedIncident.camera_id}
                  </Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2" color="text.secondary">
                    时间戳
                  </Typography>
                  <Typography variant="body1">
                    {format(new Date(selectedIncident.timestamp * 1000), 'yyyy-MM-dd HH:mm:ss')}
                  </Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2" color="text.secondary">
                    帧号
                  </Typography>
                  <Typography variant="body1">
                    {selectedIncident.frame_id}
                  </Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2" color="text.secondary">
                    重叠率
                  </Typography>
                  <Typography variant="body1">
                    {(selectedIncident.overlap_ratio * 100).toFixed(2)}%
                  </Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2" color="text.secondary">
                    状态
                  </Typography>
                  <Typography variant="body1">
                    {selectedIncident.status}
                  </Typography>
                </Grid>
                {selectedIncident.vlm_confidence && (
                  <Grid item xs={6}>
                    <Typography variant="body2" color="text.secondary">
                      VLM 置信度
                    </Typography>
                    <Typography variant="body1">
                      {(selectedIncident.vlm_confidence * 100).toFixed(2)}%
                    </Typography>
                  </Grid>
                )}
                {selectedIncident.vlm_summary && (
                  <Grid item xs={12}>
                    <Typography variant="body2" color="text.secondary">
                      VLM 描述
                    </Typography>
                    <Typography variant="body1">
                      {selectedIncident.vlm_summary}
                    </Typography>
                  </Grid>
                )}
              </Grid>
            </DialogContent>
            <DialogActions>
              <Button onClick={() => setDetailDialogOpen(false)}>
                关闭
              </Button>
            </DialogActions>
          </>
        )}
      </Dialog>
    </Box>
  );
};

export default IncidentPage;
