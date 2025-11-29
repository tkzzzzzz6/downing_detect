"""Detection API endpoints"""
from fastapi import APIRouter, HTTPException
from loguru import logger

from backend.models import (
    DetectionStartRequest,
    DetectionStartResponse,
    DetectionStopResponse,
    DetectionStatusResponse
)
from backend.services.detection_service import detection_service

router = APIRouter(prefix="/api/detection", tags=["detection"])


@router.post("/start", response_model=DetectionStartResponse)
async def start_detection(request: DetectionStartRequest):
    """Start a new detection session"""
    try:
        session_id = await detection_service.start_detection(
            video_source=request.video_source,
            is_webcam=request.is_webcam
        )
        return DetectionStartResponse(
            session_id=session_id,
            status="started",
            message="Detection started successfully"
        )
    except FileNotFoundError as e:
        logger.error(f"Video file not found: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        logger.error(f"Detection already running: {e}")
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to start detection: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start detection: {str(e)}")


@router.post("/stop", response_model=DetectionStopResponse)
async def stop_detection():
    """Stop current detection session"""
    try:
        result = await detection_service.stop_detection()
        return DetectionStopResponse(**result)
    except RuntimeError as e:
        logger.error(f"No active detection session: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to stop detection: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to stop detection: {str(e)}")


@router.get("/status", response_model=DetectionStatusResponse)
async def get_detection_status():
    """Get current detection status"""
    try:
        status = detection_service.get_status()
        return DetectionStatusResponse(**status)
    except Exception as e:
        logger.error(f"Failed to get detection status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")
