import threading
import time
from dataclasses import dataclass, field
from queue import Full, Queue
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np
from loguru import logger

from .vlm_client import VLMClient, VLMResponse


@dataclass
class VLMTask:
    frame_id: int
    timestamp: float
    camera_id: str
    overlap_ratio: float
    bbox: Tuple[int, int, int, int]
    image_crop: np.ndarray
    extra_metadata: Dict[str, Any] = field(default_factory=dict)
    incident_id: Optional[str] = None


@dataclass
class VLMTaskResult:
    task: VLMTask
    response: Optional[VLMResponse] = None
    error: Optional[Exception] = None


CallbackType = Callable[[VLMTaskResult], None]


class VLMWorker:
    """Background worker consuming VLM tasks without blocking the main video loop."""

    def __init__(
        self,
        vlm_client: VLMClient,
        prompt_template: str,
        max_queue_size: int = 32,
        worker_name: str = "vlm_worker",
    ) -> None:
        self.vlm_client = vlm_client
        self.prompt_template = prompt_template
        self.queue: Queue[VLMTask] = Queue(maxsize=max_queue_size)
        self.callbacks: List[CallbackType] = []
        self._thread: Optional[threading.Thread] = None
        self._running = False
        self.worker_name = worker_name

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run, name="vlm-worker", daemon=True)
        self._thread.start()

    def stop(self, timeout: float = 2.0) -> None:
        if not self._running:
            return
        self._running = False
        sentinel = VLMTask(
            frame_id=-1,
            timestamp=time.time(),
            camera_id="__sentinel__",
            overlap_ratio=0.0,
            bbox=(0, 0, 0, 0),
            image_crop=np.zeros((1, 1, 3), dtype=np.uint8),
        )
        try:
            self.queue.put_nowait(sentinel)
        except Full:
            logger.debug("VLM queue full while stopping; sentinel skipped.")
        if self._thread:
            self._thread.join(timeout=timeout)
            self._thread = None

    def submit(self, task: VLMTask, block: bool = False, timeout: float = 0.0) -> bool:
        if not self._running:
            logger.warning("VLMWorker is not running; task dropped.")
            return False
        try:
            self.queue.put(task, block=block, timeout=timeout)
            return True
        except Full:
            logger.warning("VLM task queue full; dropping task frame_id=%s camera=%s", task.frame_id, task.camera_id)
            return False

    def register_callback(self, callback: CallbackType) -> None:
        self.callbacks.append(callback)

    @property
    def is_running(self) -> bool:
        return self._running

    def _run(self) -> None:
        while self._running:
            task = self.queue.get()
            if not self._running or task.camera_id == "__sentinel__":
                break
            result = self._execute_task(task)
            for callback in self.callbacks:
                try:
                    callback(result)
                except Exception as callback_error:  # pragma: no cover - defensive
                    logger.exception("VLM callback error: %s", callback_error)
        logger.info("VLMWorker stopped.")

    def _execute_task(self, task: VLMTask) -> VLMTaskResult:
        metadata = {
            "camera_id": task.camera_id,
            "overlap_ratio": round(task.overlap_ratio, 3),
            **task.extra_metadata,
        }
        try:
            start_time = time.time()
            response = self.vlm_client.generate_description(
                image=task.image_crop,
                prompt=self.prompt_template,
                metadata=metadata,
            )
            latency = time.time() - start_time
            return VLMTaskResult(task=task, response=response)
        except Exception as exc:  # pragma: no cover - logging side effect
            logger.warning(
                "VLM task failed (frame_id=%s camera=%s): %s",
                task.frame_id,
                task.camera_id,
                exc,
            )
            return VLMTaskResult(task=task, error=exc)

