"""Detection service for managing video detection sessions"""
import asyncio
import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Optional, Union, Dict, Any
from pathlib import Path
from loguru import logger

from backend.core.video_processor import VideoProcessor
from backend.core.incident_manager import IncidentManager
from backend.core.vlm_worker import VLMWorker
from backend.core.vlm_client import VLMClient, VLMProvider
from backend.core.email_notifier import EmailNotifier
from backend.core.settings import load_settings
from backend.services.websocket_manager import ws_manager
from backend.core.logger import (
    log_detection_start,
    log_detection_stop,
    log_video_info,
    log_drowning_alert,
    log_section_header,
)

# Import camera_service for preview management
from backend.services.camera_service import camera_service


@dataclass
class DetectionSession:
    """Represents an active detection session"""
    session_id: str
    video_source: Union[str, int]
    is_webcam: bool
    start_time: float
    processor: VideoProcessor
    thread: threading.Thread
    status: str = "running"  # "running", "stopping", "stopped"
    statistics: Dict[str, Any] = field(default_factory=dict)
    current_frame: int = 0
    fps: float = 0.0
    end_time: Optional[float] = None  # 停止时的时间戳
    camera_index: Optional[int] = None  # 摄像头索引，用于重启预览


class DetectionService:
    """Manages video detection sessions"""

    def __init__(self):
        self.current_session: Optional[DetectionSession] = None
        self.session_lock = threading.Lock()
        self._stop_event = threading.Event()

    async def start_detection(
        self,
        video_source: Union[str, int],
        is_webcam: bool = False
    ) -> str:
        """Start a new detection session"""
        with self.session_lock:
            if self.current_session and self.current_session.status == "running":
                raise RuntimeError("Detection session already in progress")

            # Clear previous stopped session
            self.current_session = None

            # If using webcam, stop any preview that might be using the camera
            if is_webcam:
                try:
                    camera_index = int(video_source)
                    logger.info(f"Stopping preview for camera {camera_index} before starting detection")
                    camera_service.stop_preview(camera_index)
                    # Give the camera a moment to be released
                    await asyncio.sleep(0.3)
                except Exception as e:
                    logger.warning(f"Failed to stop camera preview: {e}")

            # Validate video source
            if not is_webcam and not Path(video_source).exists():
                raise FileNotFoundError(f"Video file not found: {video_source}")

            # Setup notification pipeline
            settings = load_settings()
            email_notifier = EmailNotifier(settings.email) if settings.email.enabled else None
            incident_manager = IncidentManager(
                output_dir=settings.incident_output_dir,
                email_notifier=email_notifier
            )

            # Setup VLM if enabled
            vlm_worker = None
            vlm_client = None
            vlm_config = settings.vlm
            if vlm_config.enabled:
                try:
                    provider = VLMProvider(vlm_config.provider)
                    vlm_client = VLMClient(
                        provider=provider,
                        model=vlm_config.model,
                        api_key=vlm_config.api_key,
                        base_url=vlm_config.base_url,
                        timeout=vlm_config.timeout,
                        max_retries=vlm_config.max_retries,
                    )
                    vlm_worker = VLMWorker(
                        vlm_client,
                        vlm_config.prompt_template,
                        worker_name=f"vlm_worker_{provider.value}",
                    )
                    vlm_worker.register_callback(incident_manager.handle_vlm_result)
                    # Register callback for WebSocket alerts
                    vlm_worker.register_callback(self._vlm_alert_callback)
                except Exception as e:
                    logger.warning(f"Failed to initialize VLM: {e}")

            # Create output path
            output_dir = Path("output")
            output_dir.mkdir(exist_ok=True)
            output_path = str(output_dir / ("webcam_output.mp4" if is_webcam else "output_video.mp4"))

            # Create session first
            session_id = uuid.uuid4().hex
            self._stop_event.clear()

            # Create session object
            session = DetectionSession(
                session_id=session_id,
                video_source=video_source,
                is_webcam=is_webcam,
                start_time=time.time(),
                processor=None,  # Will be set below
                thread=None,  # Will be set below
                camera_index=int(video_source) if is_webcam else None
            )

            # Create video processor with WebSocket integration and session reference
            processor = WebSocketVideoProcessor(
                video_source=video_source,
                output_path=output_path,
                is_webcam=is_webcam,
                incident_manager=incident_manager,
                vlm_worker=vlm_worker,
                ws_manager=ws_manager,
                stop_event=self._stop_event,
                session=session
            )

            # Start processing in background thread
            thread = threading.Thread(
                target=self._run_detection,
                args=(processor, session_id),
                daemon=True
            )
            thread.start()

            # Update session with processor and thread
            session.processor = processor
            session.thread = thread

            self.current_session = session

            # 使用美化的日志
            log_detection_start(session_id, str(video_source), is_webcam)
            await ws_manager.send_status("running", f"Detection started for {video_source}")

            return session_id

    def _run_detection(self, processor: VideoProcessor, session_id: str):
        """Run detection in background thread"""
        try:
            processor.process_video()
            logger.info(f"Detection completed: {session_id}")
        except Exception as e:
            logger.error(f"Detection error: {e}")
            asyncio.run(ws_manager.send_error(str(e)))
        finally:
            # Stop VLM worker if it exists
            if processor.vlm_worker:
                try:
                    processor.vlm_worker.stop(timeout=1.0)
                except Exception as e:
                    logger.warning(f"Error stopping VLM worker: {e}")

            with self.session_lock:
                if self.current_session:
                    self.current_session.status = "stopped"

    async def stop_detection(self) -> Dict[str, Any]:
        """Stop current detection session"""
        with self.session_lock:
            if not self.current_session:
                raise RuntimeError("No active detection session")

            session = self.current_session
            session.status = "stopping"

        # Signal stop
        self._stop_event.set()

        # Wait for thread to finish (with timeout)
        # Use shorter timeout to avoid hanging on Ctrl+C
        session.thread.join(timeout=3.0)

        # If thread is still alive, log warning but continue
        if session.thread.is_alive():
            logger.warning(f"Detection thread did not stop within timeout, forcing cleanup")

        # Record end time
        session.end_time = time.time()
        elapsed_time = session.end_time - session.start_time

        # Calculate final FPS
        if elapsed_time > 0:
            session.fps = session.current_frame / elapsed_time

        # Calculate statistics
        statistics = {
            "total_frames": session.current_frame,
            "processing_time": elapsed_time,
            "average_fps": session.fps,
            "incidents_detected": 0  # TODO: Track this
        }

        session.statistics = statistics
        session.status = "stopped"

        # 使用美化的日志
        log_detection_stop(session.session_id, session.current_frame, elapsed_time)
        await ws_manager.send_status("stopped", "Detection stopped")

        # Keep session for a short time so frontend can retrieve final stats
        # Frontend will see status="stopped" with final fps and elapsed_time
        # Session will be cleared on next start

        return {
            "status": "stopped",
            "statistics": statistics
        }

    def get_status(self) -> Dict[str, Any]:
        """Get current detection status"""
        with self.session_lock:
            if not self.current_session:
                return {
                    "status": "idle",
                    "session_id": None,
                    "current_frame": 0,
                    "fps": 0.0,
                    "elapsed_time": 0.0,
                    "video_source": None
                }

            session = self.current_session

            # 如果已停止，使用记录的end_time；否则实时计算
            if session.end_time is not None:
                elapsed_time = session.end_time - session.start_time
            else:
                elapsed_time = time.time() - session.start_time

            return {
                "status": session.status,
                "session_id": session.session_id,
                "current_frame": session.current_frame,
                "fps": session.fps,
                "elapsed_time": elapsed_time,
                "video_source": str(session.video_source)
            }

    async def _vlm_alert_callback(self, result):
        """Callback for VLM results to send WebSocket alerts"""
        if result.error:
            return

        task = result.task
        await ws_manager.send_alert({
            "message": "Drowning danger detected!",
            "incident_id": task.incident_id or "",
            "overlap_ratio": task.overlap_ratio,
            "camera_id": task.camera_id,
            "timestamp": task.timestamp
        })


class WebSocketVideoProcessor(VideoProcessor):
    """Extended VideoProcessor that sends updates via WebSocket"""

    def __init__(self, *args, ws_manager=None, stop_event=None, session=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.ws_manager = ws_manager
        self.stop_event = stop_event
        self.session = session
        self.last_frame_send_time = 0
        self.frame_send_interval = 0.2  # Send frames every 0.2 seconds (5 FPS)
        self.last_fps_update_time = 0
        self.fps_update_interval = 1.0  # Update FPS every 1 second

    async def send_frame_update(self, annotated_frame, frame_id: int, detections: dict):
        """Send frame update via WebSocket"""
        if not self.ws_manager:
            return

        import cv2
        import base64

        try:
            # Resize frame for transmission (reduce bandwidth)
            height, width = annotated_frame.shape[:2]
            max_width = 640
            if width > max_width:
                scale = max_width / width
                new_width = max_width
                new_height = int(height * scale)
                frame_resized = cv2.resize(annotated_frame, (new_width, new_height))
            else:
                frame_resized = annotated_frame

            # Encode frame to JPEG
            _, buffer = cv2.imencode('.jpg', frame_resized, [cv2.IMWRITE_JPEG_QUALITY, 70])
            frame_base64 = base64.b64encode(buffer).decode('utf-8')

            # Send via WebSocket
            await self.ws_manager.send_frame_update({
                "frame_id": frame_id,
                "timestamp": time.time(),
                "image": f"data:image/jpeg;base64,{frame_base64}",
                "detections": detections
            })
        except Exception as e:
            logger.warning(f"Failed to send frame update: {e}")

    def process_video(self):
        """Override to send WebSocket updates with video frames"""
        import cv2
        from backend.core.detection_utils import (
            calculate_overlap_ratio,
            draw_info,
            draw_person_boxes,
            draw_river_mask,
            draw_warning,
        )
        from backend.core.vlm_worker import VLMTask
        from tqdm import tqdm

        # 使用专业的日志
        log_section_header("Video Processing Started")
        logger.info(f"Camera ID     : {self.camera_id}")
        logger.info(f"Output Path   : {self.output_path}")
        log_video_info(self.fps, self.width, self.height, self.total_frames)

        frame_count = 0
        pbar = tqdm(total=self.total_frames, desc="Processing video", unit="frames") if self.total_frames else None

        while True:
            # Check for stop signal
            if self.stop_event and self.stop_event.is_set():
                logger.info(f"Stop signal detected, terminating video processing. Processed {frame_count} frames")
                break

            ret, frame = self.cap.read()
            if not ret:
                if self.is_webcam:
                    logger.debug("Webcam read failed, retrying...")
                    continue
                else:
                    logger.info(f"Video processing completed. Total frames processed: {frame_count}")
                    break

            current_time = time.time()

            # Run detection
            results_river = self.model_loader.get_river_model().track(
                source=frame, show=False, tracker="bytetrack.yaml", verbose=False
            )
            results_person = self.model_loader.get_person_model().track(
                source=frame, show=False, tracker="bytetrack.yaml", verbose=False
            )

            annotated_frame = frame.copy()

            river_mask = draw_river_mask(annotated_frame, results_river[0].masks if results_river[0].masks is not None else None)
            person_detected, person_masks, person_bboxes = draw_person_boxes(
                annotated_frame,
                results_person[0].boxes if results_person[0].boxes is not None else None,
                river_mask
            )

            max_overlap_ratio = 0
            best_bbox = None
            if person_detected and person_masks:
                for person_mask, bbox in zip(person_masks, person_bboxes):
                    overlap_ratio = calculate_overlap_ratio(person_mask, river_mask)
                    if overlap_ratio > max_overlap_ratio:
                        max_overlap_ratio = overlap_ratio
                        best_bbox = bbox

            # Handle warnings and incidents
            if max_overlap_ratio > 0.90:
                self.last_detection_time = current_time
                incident_id = self._ensure_incident(
                    annotated_frame, best_bbox, max_overlap_ratio, current_time, frame_count
                )
                # 使用美化的警报日志
                log_drowning_alert(frame_count, max_overlap_ratio, incident_id)
                self._maybe_dispatch_vlm_task(
                    frame, best_bbox, max_overlap_ratio, current_time, frame_count, incident_id
                )
                if not self.warning_active:
                    self.warning_active = True
                    self.warning_start_time = current_time
                    self.info_message = f"Warning: Drowning danger detected! Overlap ratio: {max_overlap_ratio:.2f}"
                    self.print_warning(self.info_message)

            if self.warning_active:
                draw_warning(annotated_frame)

                if current_time - self.last_print_time >= self.print_interval:
                    self.print_warning(self.info_message)
                    self.last_print_time = current_time

                if current_time - self.last_detection_time > self.detection_window:
                    self.warning_active = False
                    self.info_message = "Warning cleared: Detection window time exceeded"
                    self.print_warning_cleared(self.info_message)
                    self._reset_incident_tracking()

            if self.warning_active and current_time - self.warning_start_time > self.warning_duration:
                self.warning_active = False
                self.info_message = "Warning cleared: Warning duration exceeded"
                self.print_warning_cleared(self.info_message)
                self._reset_incident_tracking()

            draw_info(annotated_frame, self.info_message)

            # Send frame via WebSocket at reduced rate
            if current_time - self.last_frame_send_time >= self.frame_send_interval:
                asyncio.run(self.send_frame_update(
                    annotated_frame,
                    frame_count,
                    {
                        "person_detected": person_detected,
                        "overlap_ratio": max_overlap_ratio,
                        "warning_active": self.warning_active
                    }
                ))
                self.last_frame_send_time = current_time

            self.out.write(annotated_frame)

            frame_count += 1
            if pbar:
                pbar.update(1)

            # Update session statistics
            if self.session:
                self.session.current_frame = frame_count

                # Update FPS every second
                if current_time - self.last_fps_update_time >= self.fps_update_interval:
                    elapsed = current_time - self.session.start_time
                    if elapsed > 0:
                        self.session.fps = frame_count / elapsed
                    self.last_fps_update_time = current_time

        if pbar:
            pbar.close()
        self.cleanup()


# Global detection service instance
detection_service = DetectionService()
