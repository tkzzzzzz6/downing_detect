"""Pydantic models for API requests and responses"""
from pydantic import BaseModel, Field
from typing import Optional, List, Union, Dict, Any
from datetime import datetime


# Detection API Models
class DetectionStartRequest(BaseModel):
    video_source: Union[str, int] = Field(..., description="Video file path or camera index")
    is_webcam: bool = Field(default=False, description="Whether the source is a webcam")


class DetectionStartResponse(BaseModel):
    session_id: str
    status: str
    message: str


class DetectionStopResponse(BaseModel):
    status: str
    statistics: Dict[str, Any]


class DetectionStatusResponse(BaseModel):
    status: str  # "running", "idle", "stopping"
    session_id: Optional[str] = None
    current_frame: int = 0
    fps: float = 0.0
    elapsed_time: float = 0.0
    video_source: Optional[str] = None


# Incident API Models
class IncidentResponse(BaseModel):
    incident_id: str
    camera_id: str
    frame_id: int
    timestamp: float
    overlap_ratio: float
    bbox: List[int]
    screenshot_url: str
    vlm_summary: Optional[str] = None
    vlm_confidence: Optional[float] = None
    status: str
    extra_metadata: Dict[str, Any] = Field(default_factory=dict)


class IncidentListResponse(BaseModel):
    total: int
    page: int
    limit: int
    incidents: List[IncidentResponse]


# Configuration API Models
class EmailConfig(BaseModel):
    smtp_server: str = ""
    smtp_port: int = 465
    username: str = ""
    password: str = ""
    sender: str = ""
    recipients: List[str] = Field(default_factory=list)
    use_tls: bool = True
    enabled: bool = False


class VLMConfig(BaseModel):
    provider: Optional[str] = None
    model: str = "gpt-4o-mini"
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    prompt_template: str = "请描述画面中的溺水风险、人物位置以及环境。"
    timeout: float = 15.0
    max_retries: int = 2
    enabled: bool = False


class LoggingConfig(BaseModel):
    level: str = "INFO"
    console_level: Optional[str] = None
    log_dir: str = "logs"
    file_pattern: str = "app_{time:YYYY-MM-DD}.log"
    rotation: str = "10 MB"
    retention: str = "7 days"


class ConfigResponse(BaseModel):
    incident_output_dir: str
    email: EmailConfig
    vlm: VLMConfig
    logging: LoggingConfig


class ConfigUpdateRequest(BaseModel):
    incident_output_dir: Optional[str] = None
    email: Optional[Dict[str, Any]] = None
    vlm: Optional[Dict[str, Any]] = None
    logging: Optional[Dict[str, Any]] = None


# WebSocket Message Models
class WebSocketMessage(BaseModel):
    type: str
    data: Dict[str, Any] = Field(default_factory=dict)


class FrameUpdate(BaseModel):
    type: str = "frame"
    frame_id: int
    timestamp: float
    detections: Dict[str, Any]


class AlertMessage(BaseModel):
    type: str = "alert"
    severity: str
    message: str
    incident_id: str
    overlap_ratio: float
    camera_id: str
    timestamp: float


class StatusUpdate(BaseModel):
    type: str = "status"
    status: str
    message: str


class ErrorMessage(BaseModel):
    type: str = "error"
    error: str
    details: Optional[str] = None
