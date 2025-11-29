/**
 * API client for communicating with backend
 */
import axios, { AxiosInstance } from 'axios';

const BACKEND_URL = 'http://127.0.0.1:8000';

class APIClient {
  private client: AxiosInstance;
  private ws: WebSocket | null = null;
  private wsCallbacks: Map<string, Function[]> = new Map();

  constructor() {
    this.client = axios.create({
      baseURL: BACKEND_URL,
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }

  // Detection API
  async startDetection(videoSource: string | number, isWebcam: boolean = false) {
    const response = await this.client.post('/api/detection/start', {
      video_source: videoSource,
      is_webcam: isWebcam,
    });
    return response.data;
  }

  async stopDetection() {
    const response = await this.client.post('/api/detection/stop');
    return response.data;
  }

  async getDetectionStatus() {
    const response = await this.client.get('/api/detection/status');
    return response.data;
  }

  // Incident API
  async getIncidents(page: number = 1, limit: number = 20, startDate?: number, endDate?: number) {
    const params: any = { page, limit };
    if (startDate) params.start_date = startDate;
    if (endDate) params.end_date = endDate;

    const response = await this.client.get('/api/incidents', { params });
    return response.data;
  }

  async getIncident(incidentId: string) {
    const response = await this.client.get(`/api/incidents/${incidentId}`);
    return response.data;
  }

  async deleteIncident(incidentId: string) {
    const response = await this.client.delete(`/api/incidents/${incidentId}`);
    return response.data;
  }

  getIncidentScreenshotUrl(incidentId: string): string {
    return `${BACKEND_URL}/api/incidents/${incidentId}/screenshot`;
  }

  // Configuration API
  async getConfig() {
    const response = await this.client.get('/api/config');
    return response.data;
  }

  async updateConfig(config: any) {
    const response = await this.client.put('/api/config', config);
    return response.data;
  }

  // WebSocket
  connectWebSocket() {
    if (this.ws) {
      this.ws.close();
    }

    this.ws = new WebSocket(`ws://127.0.0.1:8000/ws`);

    this.ws.onopen = () => {
      console.log('WebSocket connected');
      this.triggerCallbacks('connect', {});
    };

    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      console.log('WebSocket message:', data);
      this.triggerCallbacks(data.type, data);
    };

    this.ws.onclose = () => {
      console.log('WebSocket disconnected');
      this.triggerCallbacks('disconnect', {});
      // Auto reconnect after 3 seconds
      setTimeout(() => {
        console.log('Attempting to reconnect WebSocket...');
        this.connectWebSocket();
      }, 3000);
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      this.triggerCallbacks('error', error);
    };
  }

  disconnectWebSocket() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  onWebSocketMessage(type: string, callback: Function) {
    if (!this.wsCallbacks.has(type)) {
      this.wsCallbacks.set(type, []);
    }
    this.wsCallbacks.get(type)!.push(callback);
  }

  offWebSocketMessage(type: string, callback: Function) {
    const callbacks = this.wsCallbacks.get(type);
    if (callbacks) {
      const index = callbacks.indexOf(callback);
      if (index > -1) {
        callbacks.splice(index, 1);
      }
    }
  }

  private triggerCallbacks(type: string, data: any) {
    const callbacks = this.wsCallbacks.get(type);
    if (callbacks) {
      callbacks.forEach(callback => callback(data));
    }
  }

  // Health check
  async healthCheck() {
    try {
      const response = await this.client.get('/health');
      return response.data;
    } catch (error) {
      throw new Error('Backend is not running');
    }
  }
}

export const apiClient = new APIClient();
export default apiClient;
