import cv2
import time
from typing import Optional, Tuple
from loguru import logger
from tqdm import tqdm

from backend.core.detection_utils import (
    calculate_overlap_ratio,
    draw_info,
    draw_person_boxes,
    draw_river_mask,
    draw_warning,
)
from backend.core.incident_manager import IncidentManager
from backend.core.model_loader import ModelLoader
from backend.core.vlm_worker import VLMTask, VLMWorker

class VideoProcessor:
    def __init__(
        self,
        video_source,
        output_path,
        is_webcam=False,
        vlm_worker: Optional[VLMWorker] = None,
        camera_id: Optional[str] = None,
        incident_manager: Optional[IncidentManager] = None,
    ):
        self.video_source = video_source
        self.output_path = output_path
        self.is_webcam = is_webcam
        self.vlm_worker = vlm_worker
        self.camera_id = camera_id or (f"webcam_{video_source}" if is_webcam else str(video_source))
        self.incident_manager = incident_manager

        # Open video capture (support both webcam and video file)
        if self.is_webcam:
            # Convert to int if it's a webcam index
            camera_index = int(video_source) if isinstance(video_source, (int, str)) else 0
            logger.info(f"Opening webcam with index: {camera_index}")
            self.cap = cv2.VideoCapture(camera_index)

            # Configure webcam for better performance
            if self.cap.isOpened():
                # Set buffer size to 1 to get latest frame
                self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                # Try to set higher resolution if supported
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        else:
            logger.info(f"Opening video file: {video_source}")
            self.cap = cv2.VideoCapture(video_source)

        # Check if video source was opened successfully
        if not self.cap.isOpened():
            error_msg = f"Failed to open {'webcam' if is_webcam else 'video file'}: {video_source}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        
        self.fps = int(self.cap.get(cv2.CAP_PROP_FPS))
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        self.out = cv2.VideoWriter(output_path, fourcc, self.fps, (self.width, self.height))
        
        self.model_loader = ModelLoader()
        
        self.warning_active = False
        self.last_detection_time = 0
        self.warning_start_time = 0
        self.warning_duration = 15
        self.detection_window = 30
        self.info_message = ""
        self.last_print_time = 0
        self.print_interval = 5  # 每秒打印一次警告信息
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT)) if not is_webcam else None
        if self.vlm_worker and not self.vlm_worker.is_running:
            self.vlm_worker.start()
        self.current_incident_id: Optional[str] = None
        self.incident_vlm_dispatched = False

    def process_video(self):
        logger.info(f"开始处理视频 - 摄像头ID: {self.camera_id}, 输出路径: {self.output_path}")
        logger.info(f"视频参数 - FPS: {self.fps}, 分辨率: {self.width}x{self.height}, 总帧数: {self.total_frames}")
        
        frame_count = 0
        pbar = tqdm(total=self.total_frames, desc="Processing video", unit="frames") if self.total_frames else None
        
        while True:
            ret, frame = self.cap.read()
            if not ret:
                if self.is_webcam:
                    logger.debug("摄像头读取失败，继续尝试...")
                    continue
                else:
                    logger.info(f"视频处理完成，共处理 {frame_count} 帧")
                    break

            current_time = time.time()

            results_river = self.model_loader.get_river_model().track(
                source=frame, show=False, tracker="bytetrack.yaml", verbose=False
            )
            results_person = self.model_loader.get_person_model().track(
                source=frame, show=False, tracker="bytetrack.yaml", verbose=False
            )

            annotated_frame = frame.copy()
            
            river_mask = draw_river_mask(annotated_frame, results_river[0].masks if results_river[0].masks is not None else None)
            person_detected, person_masks, person_bboxes = draw_person_boxes(annotated_frame, 
                                                              results_person[0].boxes if results_person[0].boxes is not None else None, 
                                                              river_mask)

            max_overlap_ratio = 0
            best_bbox: Optional[Tuple[int, int, int, int]] = None
            if person_detected and person_masks:
                for person_mask, bbox in zip(person_masks, person_bboxes):
                    overlap_ratio = calculate_overlap_ratio(person_mask, river_mask)
                    if overlap_ratio > max_overlap_ratio:
                        max_overlap_ratio = overlap_ratio
                        best_bbox = bbox

            if max_overlap_ratio > 0.90:
                logger.warning(
                    f"检测到溺水危险 - 帧ID: {frame_count}, 重叠比例: {max_overlap_ratio:.2f}, "
                    f"边界框: {best_bbox}, 摄像头: {self.camera_id}"
                )
                self.last_detection_time = current_time
                incident_id = self._ensure_incident(
                    annotated_frame, best_bbox, max_overlap_ratio, current_time, frame_count
                )
                self._maybe_dispatch_vlm_task(
                    frame,
                    best_bbox,
                    max_overlap_ratio,
                    current_time,
                    frame_count,
                    incident_id,
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

            self.out.write(annotated_frame)

            frame_count += 1
            if pbar:
                pbar.update(1)

        if pbar:
            pbar.close()
        self.cleanup()

    def print_warning(self, message):
        # 打印多行警告信息，使其更加显眼
        logger.warning(message)
        print("\n" + "=" * 50)
        for _ in range(1):
            print(f"\033[91m{message}\033[0m")  # 红色文字输出警告信息
        print("=" * 50 + "\n")

    def print_warning_cleared(self, message):
        # 打印多行警告解除信息，使其更加显眼
        logger.info(message)
        print("\n" + "=" * 50)
        for _ in range(1):
            print(f"\033[93m{message}\033[0m")  # 黄色文字输出警告解除信息
        print("=" * 50 + "\n")

    def cleanup(self):
        logger.info("Cleaning up video processor resources...")
        import time

        # Release video capture (may hang on webcam, use timeout protection)
        try:
            if self.cap is not None:
                if self.cap.isOpened():
                    self.cap.release()
                    logger.debug("Video capture released")
                    # Give the camera time to fully release
                    time.sleep(0.3)
                self.cap = None
        except Exception as e:
            logger.error(f"Error releasing video capture: {e}")

        # Release video writer
        try:
            if self.out is not None:
                self.out.release()
                logger.debug("Video writer released")
                self.out = None
        except Exception as e:
            logger.error(f"Error releasing video writer: {e}")

        # Destroy all OpenCV windows
        try:
            import cv2
            cv2.destroyAllWindows()
        except Exception as e:
            logger.debug(f"Error destroying OpenCV windows: {e}")

        logger.info("Video processor cleanup complete")

    def _maybe_dispatch_vlm_task(
        self,
        frame,
        bbox: Optional[Tuple[int, int, int, int]],
        overlap_ratio: float,
        timestamp: float,
        frame_id: int,
        incident_id: Optional[str],
    ):
        if bbox is None or incident_id is None:
            return
        if not self.vlm_worker:
            if self.incident_manager:
                self.incident_manager.finalize_without_vlm(
                    incident_id, "VLM 未启用，已使用YOLO数据生成告警。"
                )
            return
        if self.incident_vlm_dispatched:
            return
        x1, y1, x2, y2 = bbox
        x1 = max(0, min(self.width - 1, x1))
        x2 = max(0, min(self.width, x2))
        y1 = max(0, min(self.height - 1, y1))
        y2 = max(0, min(self.height, y2))
        if x2 <= x1 or y2 <= y1:
            return
        crop = frame[y1:y2, x1:x2].copy()
        task = VLMTask(
            frame_id=frame_id,
            timestamp=timestamp,
            camera_id=self.camera_id,
            overlap_ratio=overlap_ratio,
            bbox=(x1, y1, x2, y2),
            image_crop=crop,
            extra_metadata={
                "is_webcam": self.is_webcam,
                "warning_active": self.warning_active,
            },
            incident_id=incident_id,
        )
        success = self.vlm_worker.submit(task, block=False)
        if not success:
            logger.debug("Failed to submit VLM task frame_id=%s camera=%s", frame_id, self.camera_id)
        else:
            self.incident_vlm_dispatched = True

    def _ensure_incident(
        self,
        annotated_frame,
        bbox: Optional[Tuple[int, int, int, int]],
        overlap_ratio: float,
        timestamp: float,
        frame_id: int,
    ) -> Optional[str]:
        if not self.incident_manager or bbox is None:
            return None
        if self.current_incident_id:
            return self.current_incident_id
        record = self.incident_manager.create_incident(
            camera_id=self.camera_id,
            frame_id=frame_id,
            timestamp=timestamp,
            overlap_ratio=overlap_ratio,
            bbox=bbox,
            annotated_frame=annotated_frame.copy(),
            extra_metadata={"video_source": str(self.video_source)},
        )
        self.current_incident_id = record.incident_id
        self.incident_vlm_dispatched = False
        if not self.vlm_worker:
            self.incident_manager.finalize_without_vlm(
                self.current_incident_id,
                "VLM 未启用，使用 YOLO 元数据发送告警。",
            )
        return self.current_incident_id

    def _reset_incident_tracking(self):
        self.current_incident_id = None
        self.incident_vlm_dispatched = False