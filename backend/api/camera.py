"""Camera API endpoints"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from typing import List, Optional
from loguru import logger

from backend.services.camera_service import camera_service


router = APIRouter(prefix="/api/camera", tags=["camera"])


class CameraInfo(BaseModel):
    """Camera information"""
    index: int
    name: str
    width: int
    height: int
    fps: int
    available: bool


class CameraListResponse(BaseModel):
    """Camera list response"""
    cameras: List[CameraInfo]


class PreviewResponse(BaseModel):
    """Preview response"""
    success: bool
    message: str


@router.get("/list", response_model=CameraListResponse)
async def list_cameras():
    """List all available cameras"""
    try:
        cameras = camera_service.list_cameras()
        return CameraListResponse(cameras=cameras)
    except Exception as e:
        logger.error(f"Failed to list cameras: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list cameras: {str(e)}")


@router.post("/preview/start/{camera_index}", response_model=PreviewResponse)
async def start_preview(camera_index: int):
    """Start camera preview"""
    try:
        success = camera_service.start_preview(camera_index)
        if success:
            return PreviewResponse(
                success=True,
                message=f"Preview started for camera {camera_index}"
            )
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to start preview for camera {camera_index}"
            )
    except Exception as e:
        logger.error(f"Failed to start camera preview: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/preview/stop/{camera_index}", response_model=PreviewResponse)
async def stop_preview(camera_index: int):
    """Stop camera preview"""
    try:
        success = camera_service.stop_preview(camera_index)
        return PreviewResponse(
            success=success,
            message=f"Preview {'stopped' if success else 'was not running'} for camera {camera_index}"
        )
    except Exception as e:
        logger.error(f"Failed to stop camera preview: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/preview/frame/{camera_index}")
async def get_preview_frame(camera_index: int):
    """Get preview frame"""
    try:
        frame_data = camera_service.get_preview_frame(camera_index)
        if frame_data is None:
            raise HTTPException(
                status_code=404,
                detail=f"No preview available for camera {camera_index}. Start preview first."
            )

        # Return as JSON with base64 image
        return {"image": frame_data}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get preview frame: {e}")
        raise HTTPException(status_code=500, detail=str(e))
