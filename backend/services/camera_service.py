"""Camera service for listing and previewing cameras"""
import cv2
import base64
import threading
import time
from typing import Dict, List, Optional
from loguru import logger


class CameraService:
    """Service for managing camera operations"""

    def __init__(self):
        self.preview_cameras: Dict[int, cv2.VideoCapture] = {}
        self.preview_lock = threading.Lock()

    def list_cameras(self, max_cameras: int = 10) -> List[Dict]:
        """List available cameras"""
        cameras = []

        for index in range(max_cameras):
            cap = cv2.VideoCapture(index)
            if cap.isOpened():
                # Get camera properties
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                fps = int(cap.get(cv2.CAP_PROP_FPS))

                # Try to read a frame to verify it's working
                ret, _ = cap.read()
                if ret:
                    cameras.append({
                        "index": index,
                        "name": f"Camera {index}",
                        "width": width,
                        "height": height,
                        "fps": fps if fps > 0 else 30,
                        "available": True
                    })
                    logger.debug(f"Found camera {index}: {width}x{height} @ {fps}fps")

                cap.release()
            else:
                # Stop searching after first unavailable camera
                break

        logger.info(f"Found {len(cameras)} available camera(s)")
        return cameras

    def start_preview(self, camera_index: int) -> bool:
        """Start camera preview"""
        with self.preview_lock:
            # Close existing preview for this camera
            if camera_index in self.preview_cameras:
                logger.info(f"Camera {camera_index} preview already exists, restarting")
                self._stop_preview_internal(camera_index)
                # Give it a moment to release
                time.sleep(0.2)

            # Open camera
            logger.info(f"Opening camera {camera_index} for preview")
            cap = cv2.VideoCapture(camera_index)

            # Try multiple times if first attempt fails
            if not cap.isOpened():
                logger.warning(f"First attempt to open camera {camera_index} failed, retrying...")
                cap.release()
                time.sleep(0.5)
                cap = cv2.VideoCapture(camera_index)

            if not cap.isOpened():
                logger.error(f"Failed to open camera {camera_index} for preview after retry")
                return False

            # Configure camera
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

            # Try to read a test frame
            ret, frame = cap.read()
            if not ret or frame is None:
                logger.error(f"Camera {camera_index} opened but cannot read frames")
                cap.release()
                return False

            self.preview_cameras[camera_index] = cap
            logger.info(f"Successfully started preview for camera {camera_index}")
            return True

    def _stop_preview_internal(self, camera_index: int):
        """Internal method to stop preview without lock (already locked)"""
        if camera_index in self.preview_cameras:
            try:
                cap = self.preview_cameras[camera_index]
                cap.release()
                del self.preview_cameras[camera_index]
                logger.debug(f"Stopped preview for camera {camera_index}")
            except Exception as e:
                logger.error(f"Error stopping preview for camera {camera_index}: {e}")

    def stop_preview(self, camera_index: int) -> bool:
        """Stop camera preview"""
        with self.preview_lock:
            if camera_index in self.preview_cameras:
                self._stop_preview_internal(camera_index)
                logger.info(f"Stopped preview for camera {camera_index}")
                return True
            return False

    def get_preview_frame(self, camera_index: int) -> Optional[str]:
        """Get preview frame as base64-encoded JPEG"""
        with self.preview_lock:
            if camera_index not in self.preview_cameras:
                return None

            cap = self.preview_cameras[camera_index]
            ret, frame = cap.read()

            if not ret or frame is None:
                logger.warning(f"Failed to read frame from camera {camera_index}")
                return None

            # Encode frame to JPEG
            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            frame_base64 = base64.b64encode(buffer).decode('utf-8')

            return f"data:image/jpeg;base64,{frame_base64}"

    def cleanup(self):
        """Clean up all preview cameras"""
        with self.preview_lock:
            for camera_index in list(self.preview_cameras.keys()):
                self.stop_preview(camera_index)
        logger.info("Camera service cleanup complete")


# Global camera service instance
camera_service = CameraService()
