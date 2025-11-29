"""Incident service for managing incident records"""
import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
from loguru import logger

from backend.core.incident_manager import IncidentRecord


class IncidentService:
    """Service for managing incident records and persistence"""

    def __init__(self, incident_dir: str = "output/incidents"):
        self.incident_dir = Path(incident_dir)
        self.incident_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_file = self.incident_dir / "incidents.json"
        self.incidents_cache: Dict[str, IncidentRecord] = {}
        self._load_incidents()

    def _load_incidents(self):
        """Load incidents from metadata file"""
        if not self.metadata_file.exists():
            self.incidents_cache = {}
            return

        try:
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Convert dict to IncidentRecord objects
                for incident_id, incident_data in data.items():
                    self.incidents_cache[incident_id] = IncidentRecord(**incident_data)
            logger.info(f"Loaded {len(self.incidents_cache)} incidents from metadata")
        except Exception as e:
            logger.error(f"Failed to load incidents metadata: {e}")
            self.incidents_cache = {}

    def _save_incidents(self):
        """Save incidents to metadata file"""
        try:
            data = {}
            for incident_id, incident in self.incidents_cache.items():
                # Convert IncidentRecord to dict
                data[incident_id] = {
                    "incident_id": incident.incident_id,
                    "camera_id": incident.camera_id,
                    "frame_id": incident.frame_id,
                    "timestamp": incident.timestamp,
                    "overlap_ratio": incident.overlap_ratio,
                    "bbox": list(incident.bbox),
                    "screenshot_path": incident.screenshot_path,
                    "vlm_summary": incident.vlm_summary,
                    "vlm_confidence": incident.vlm_confidence,
                    "status": incident.status,
                    "extra_metadata": incident.extra_metadata
                }

            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to save incidents metadata: {e}")

    def add_incident(self, incident: IncidentRecord):
        """Add a new incident to the cache"""
        self.incidents_cache[incident.incident_id] = incident
        self._save_incidents()

    def get_incidents(
        self,
        page: int = 1,
        limit: int = 20,
        start_date: Optional[float] = None,
        end_date: Optional[float] = None
    ) -> Dict[str, Any]:
        """Get paginated list of incidents with optional date filtering"""
        incidents = list(self.incidents_cache.values())

        # Apply date filtering
        if start_date is not None:
            incidents = [i for i in incidents if i.timestamp >= start_date]
        if end_date is not None:
            incidents = [i for i in incidents if i.timestamp <= end_date]

        # Sort by timestamp (newest first)
        incidents.sort(key=lambda x: x.timestamp, reverse=True)

        # Calculate pagination
        total = len(incidents)
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_incidents = incidents[start_idx:end_idx]

        return {
            "total": total,
            "page": page,
            "limit": limit,
            "incidents": paginated_incidents
        }

    def get_incident(self, incident_id: str) -> Optional[IncidentRecord]:
        """Get a single incident by ID"""
        return self.incidents_cache.get(incident_id)

    def delete_incident(self, incident_id: str) -> bool:
        """Delete an incident and its associated screenshot"""
        incident = self.incidents_cache.get(incident_id)
        if not incident:
            return False

        # Delete screenshot file
        screenshot_path = Path(incident.screenshot_path)
        if screenshot_path.exists():
            try:
                screenshot_path.unlink()
                logger.info(f"Deleted screenshot: {screenshot_path}")
            except Exception as e:
                logger.error(f"Failed to delete screenshot: {e}")

        # Remove from cache
        del self.incidents_cache[incident_id]
        self._save_incidents()

        logger.info(f"Deleted incident: {incident_id}")
        return True

    def get_screenshot_path(self, incident_id: str) -> Optional[Path]:
        """Get the screenshot path for an incident"""
        incident = self.incidents_cache.get(incident_id)
        if not incident:
            return None
        return Path(incident.screenshot_path)


# Global incident service instance
incident_service = IncidentService()
