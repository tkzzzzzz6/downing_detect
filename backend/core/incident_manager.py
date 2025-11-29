import threading
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional, Tuple

import cv2
from loguru import logger

from .vlm_worker import VLMTaskResult
from .logger import log_incident_created, log_vlm_response


@dataclass
class IncidentRecord:
    incident_id: str
    camera_id: str
    frame_id: int
    timestamp: float
    overlap_ratio: float
    bbox: Tuple[int, int, int, int]
    screenshot_path: str
    vlm_summary: Optional[str] = None
    vlm_confidence: Optional[float] = None
    status: str = "vlm_pending"
    extra_metadata: Dict[str, str] = field(default_factory=dict)


class IncidentManager:
    def __init__(self, output_dir: str = "output/incidents", email_notifier=None) -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.email_notifier = email_notifier
        self._records: Dict[str, IncidentRecord] = {}
        self._lock = threading.Lock()

    def create_incident(
        self,
        *,
        camera_id: str,
        frame_id: int,
        timestamp: float,
        overlap_ratio: float,
        bbox: Tuple[int, int, int, int],
        annotated_frame,
        extra_metadata: Optional[Dict[str, str]] = None,
    ) -> IncidentRecord:
        incident_id = uuid.uuid4().hex
        screenshot_path = self._save_screenshot(incident_id, annotated_frame)
        record = IncidentRecord(
            incident_id=incident_id,
            camera_id=camera_id,
            frame_id=frame_id,
            timestamp=timestamp,
            overlap_ratio=overlap_ratio,
            bbox=bbox,
            screenshot_path=screenshot_path,
            extra_metadata=extra_metadata or {},
        )
        with self._lock:
            self._records[incident_id] = record
        # 使用美化的日志
        log_incident_created(incident_id, screenshot_path)
        return record

    def handle_vlm_result(self, result: VLMTaskResult) -> None:
        incident_id = result.task.incident_id
        if not incident_id:
            logger.warning("VLM result missing incident_id; ignoring.")
            return
        record = self._records.get(incident_id)
        if not record:
            logger.warning("Incident not found for VLM result: %s", incident_id)
            return

        if result.error:
            record.status = "vlm_failed"
            record.vlm_summary = f"VLM 调用失败：{result.error}"
            record.vlm_confidence = 0.0
            logger.error(f"VLM analysis failed: {result.error}")
        else:
            record.status = "vlm_completed"
            record.vlm_summary = (result.response.summary_text or "").strip()
            record.vlm_confidence = result.response.confidence
            # 使用专业的日志
            log_vlm_response(result.response.confidence, result.response.summary_text or "")

        self._dispatch_notification(record)

    def finalize_without_vlm(self, incident_id: str, reason: str) -> None:
        record = self._records.get(incident_id)
        if not record:
            logger.warning("finalize_without_vlm called but incident not found: %s", incident_id)
            return
        if not record.vlm_summary:
            record.vlm_summary = reason
        record.status = "vlm_skipped"
        self._dispatch_notification(record)

    def _dispatch_notification(self, record: IncidentRecord) -> None:
        if self.email_notifier:
            sent = self.email_notifier.send_incident(record)
            record.status = "notified" if sent else record.status
        else:
            logger.info("Email notifier disabled; incident %s stored only.", record.incident_id)

    def _save_screenshot(self, incident_id: str, frame) -> str:
        filename = self.output_dir / f"{incident_id}.png"
        cv2.imwrite(str(filename), frame)
        return str(filename)

