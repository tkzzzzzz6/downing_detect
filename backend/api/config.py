"""Configuration management API endpoints"""
import yaml
from pathlib import Path
from fastapi import APIRouter, HTTPException
from loguru import logger

from backend.models import ConfigResponse, ConfigUpdateRequest, EmailConfig, VLMConfig, LoggingConfig
from backend.core.settings import load_settings

router = APIRouter(prefix="/api/config", tags=["configuration"])


def _mask_sensitive_data(config_dict: dict) -> dict:
    """Mask sensitive fields in configuration"""
    if "vlm" in config_dict and "api_key" in config_dict["vlm"]:
        api_key = config_dict["vlm"]["api_key"]
        if api_key:
            # Mask all but last 4 characters
            config_dict["vlm"]["api_key"] = "*" * (len(api_key) - 4) + api_key[-4:] if len(api_key) > 4 else "***"

    if "email" in config_dict and "password" in config_dict["email"]:
        password = config_dict["email"]["password"]
        if password:
            config_dict["email"]["password"] = "***"

    return config_dict


@router.get("", response_model=ConfigResponse)
async def get_config():
    """Get current configuration with sensitive data masked"""
    try:
        settings = load_settings()

        # Convert settings to dict and mask sensitive data
        config_dict = {
            "incident_output_dir": settings.incident_output_dir,
            "email": {
                "smtp_server": settings.email.smtp_server,
                "smtp_port": settings.email.smtp_port,
                "username": settings.email.username,
                "password": settings.email.password,
                "sender": settings.email.sender,
                "recipients": settings.email.recipients,
                "use_tls": settings.email.use_tls,
                "enabled": settings.email.enabled
            },
            "vlm": {
                "provider": settings.vlm.provider,
                "model": settings.vlm.model,
                "api_key": settings.vlm.api_key,
                "base_url": settings.vlm.base_url,
                "prompt_template": settings.vlm.prompt_template,
                "timeout": settings.vlm.timeout,
                "max_retries": settings.vlm.max_retries,
                "enabled": settings.vlm.enabled
            },
            "logging": {
                "level": settings.logging.level,
                "console_level": settings.logging.console_level,
                "log_dir": settings.logging.log_dir,
                "file_pattern": settings.logging.file_pattern,
                "rotation": settings.logging.rotation,
                "retention": settings.logging.retention
            }
        }

        # Mask sensitive data
        config_dict = _mask_sensitive_data(config_dict)

        return ConfigResponse(
            incident_output_dir=config_dict["incident_output_dir"],
            email=EmailConfig(**config_dict["email"]),
            vlm=VLMConfig(**config_dict["vlm"]),
            logging=LoggingConfig(**config_dict["logging"])
        )
    except Exception as e:
        logger.error(f"Failed to get configuration: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get configuration: {str(e)}")


@router.put("")
async def update_config(request: ConfigUpdateRequest):
    """Update configuration (partial update supported)"""
    try:
        config_path = Path("config/settings.yaml")
        if not config_path.exists():
            raise HTTPException(status_code=404, detail="Configuration file not found")

        # Load current config
        with open(config_path, 'r', encoding='utf-8') as f:
            current_config = yaml.safe_load(f) or {}

        # Update fields
        update_data = request.dict(exclude_none=True)

        for key, value in update_data.items():
            if key in current_config:
                if isinstance(value, dict):
                    # Merge nested dicts
                    current_config[key].update(value)
                else:
                    current_config[key] = value
            else:
                current_config[key] = value

        # Save updated config
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.safe_dump(current_config, f, allow_unicode=True, default_flow_style=False)

        # Clear settings cache to reload
        load_settings.cache_clear()

        logger.info("Configuration updated successfully")
        return {
            "status": "updated",
            "message": "Configuration updated successfully. Restart may be required for some changes."
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update configuration: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update configuration: {str(e)}")
