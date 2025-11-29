"""Incident management API endpoints"""
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from typing import Optional
from loguru import logger

from backend.models import IncidentResponse, IncidentListResponse
from backend.services.incident_service import incident_service

router = APIRouter(prefix="/api/incidents", tags=["incidents"])


@router.get("", response_model=IncidentListResponse)
async def get_incidents(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    start_date: Optional[float] = Query(None, description="Start timestamp filter"),
    end_date: Optional[float] = Query(None, description="End timestamp filter")
):
    """Get paginated list of incidents with optional date filtering"""
    try:
        result = incident_service.get_incidents(
            page=page,
            limit=limit,
            start_date=start_date,
            end_date=end_date
        )

        # Convert IncidentRecord to IncidentResponse
        incidents = [
            IncidentResponse(
                incident_id=inc.incident_id,
                camera_id=inc.camera_id,
                frame_id=inc.frame_id,
                timestamp=inc.timestamp,
                overlap_ratio=inc.overlap_ratio,
                bbox=list(inc.bbox),
                screenshot_url=f"/api/incidents/{inc.incident_id}/screenshot",
                vlm_summary=inc.vlm_summary,
                vlm_confidence=inc.vlm_confidence,
                status=inc.status,
                extra_metadata=inc.extra_metadata
            )
            for inc in result["incidents"]
        ]

        return IncidentListResponse(
            total=result["total"],
            page=result["page"],
            limit=result["limit"],
            incidents=incidents
        )
    except Exception as e:
        logger.error(f"Failed to get incidents: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get incidents: {str(e)}")


@router.get("/{incident_id}", response_model=IncidentResponse)
async def get_incident(incident_id: str):
    """Get a single incident by ID"""
    try:
        incident = incident_service.get_incident(incident_id)
        if not incident:
            raise HTTPException(status_code=404, detail="Incident not found")

        return IncidentResponse(
            incident_id=incident.incident_id,
            camera_id=incident.camera_id,
            frame_id=incident.frame_id,
            timestamp=incident.timestamp,
            overlap_ratio=incident.overlap_ratio,
            bbox=list(incident.bbox),
            screenshot_url=f"/api/incidents/{incident.incident_id}/screenshot",
            vlm_summary=incident.vlm_summary,
            vlm_confidence=incident.vlm_confidence,
            status=incident.status,
            extra_metadata=incident.extra_metadata
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get incident {incident_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get incident: {str(e)}")


@router.get("/{incident_id}/screenshot")
async def get_incident_screenshot(incident_id: str):
    """Get the screenshot image for an incident"""
    try:
        screenshot_path = incident_service.get_screenshot_path(incident_id)
        if not screenshot_path or not screenshot_path.exists():
            raise HTTPException(status_code=404, detail="Screenshot not found")

        return FileResponse(
            path=screenshot_path,
            media_type="image/png",
            filename=f"{incident_id}.png"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get screenshot for {incident_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get screenshot: {str(e)}")


@router.delete("/{incident_id}")
async def delete_incident(incident_id: str):
    """Delete an incident and its screenshot"""
    try:
        success = incident_service.delete_incident(incident_id)
        if not success:
            raise HTTPException(status_code=404, detail="Incident not found")

        return {
            "status": "deleted",
            "message": "Incident deleted successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete incident {incident_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete incident: {str(e)}")
