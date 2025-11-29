from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import List, Optional

import yaml
from pydantic import BaseModel, Field


class EmailSettings(BaseModel):
    smtp_server: str = ""
    smtp_port: int = 465
    username: str = ""
    password: str = ""
    sender: str = ""
    recipients: List[str] = Field(default_factory=list)
    use_tls: bool = True

    @property
    def enabled(self) -> bool:
        return (
            bool(self.smtp_server)
            and bool(self.username)
            and bool(self.password)
            and bool(self.sender)
            and len(self.recipients) > 0
        )


class VLMSettings(BaseModel):
    provider: Optional[str] = None
    model: str = "gpt-4o-mini"
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    prompt_template: str = "请描述画面中的溺水风险、人物位置以及环境。"
    timeout: float = 15.0
    max_retries: int = 2

    @property
    def enabled(self) -> bool:
        if not self.provider:
            return False
        if self.provider.lower() == "ollama":
            return True
        return bool(self.api_key)


class LogSettings(BaseModel):
    level: str = "INFO"
    console_level: Optional[str] = None
    log_dir: str = "logs"
    file_pattern: str = "app_{time:YYYY-MM-DD}.log"
    rotation: str = "10 MB"
    retention: str = "7 days"
    format: str = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"


class AppSettings(BaseModel):
    incident_output_dir: str = "output/incidents"
    email: EmailSettings = EmailSettings()
    vlm: VLMSettings = VLMSettings()
    logging: LogSettings = LogSettings()


def _load_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def _apply_env_overrides(data: dict) -> dict:
    overrides = {
        ("email", "smtp_server"): os.getenv("EMAIL_SMTP_SERVER"),
        ("email", "smtp_port"): os.getenv("EMAIL_SMTP_PORT"),
        ("email", "username"): os.getenv("EMAIL_USERNAME"),
        ("email", "password"): os.getenv("EMAIL_PASSWORD"),
        ("email", "sender"): os.getenv("EMAIL_SENDER"),
        ("email", "recipients"): os.getenv("EMAIL_RECIPIENTS"),
        ("email", "use_tls"): os.getenv("EMAIL_USE_TLS"),
        ("vlm", "provider"): os.getenv("VLM_PROVIDER"),
        ("vlm", "model"): os.getenv("VLM_MODEL"),
        ("vlm", "api_key"): os.getenv("VLM_API_KEY"),
        ("vlm", "base_url"): os.getenv("VLM_BASE_URL"),
        ("vlm", "prompt_template"): os.getenv("VLM_PROMPT_TEMPLATE"),
        ("vlm", "timeout"): os.getenv("VLM_TIMEOUT"),
        ("vlm", "max_retries"): os.getenv("VLM_MAX_RETRIES"),
        ("logging", "level"): os.getenv("LOG_LEVEL"),
        ("logging", "console_level"): os.getenv("LOG_CONSOLE_LEVEL"),
        ("logging", "log_dir"): os.getenv("LOG_DIR"),
        ("logging", "file_pattern"): os.getenv("LOG_FILE_PATTERN"),
        ("logging", "rotation"): os.getenv("LOG_ROTATION"),
        ("logging", "retention"): os.getenv("LOG_RETENTION"),
        ("incident_output_dir",): os.getenv("INCIDENT_OUTPUT_DIR"),
    }

    for key_path, value in overrides.items():
        if value is None:
            continue
        target = data
        *parents, leaf = key_path
        for parent in parents:
            target = target.setdefault(parent, {})
        if leaf == "recipients":
            target[leaf] = [item.strip() for item in value.split(",") if item.strip()]
        elif leaf in {"smtp_port", "max_retries"}:
            target[leaf] = int(value)
        elif leaf in {"timeout"}:
            target[leaf] = float(value)
        elif leaf == "use_tls":
            target[leaf] = value.lower() == "true"
        else:
            target[leaf] = value
    return data


@lru_cache(maxsize=1)
def load_settings(config_path: Optional[str] = None) -> AppSettings:
    path = Path(config_path or os.getenv("APP_CONFIG_PATH", "config/settings.yaml"))
    data = _load_yaml(path)
    data = _apply_env_overrides(data)
    email_data = data.get("email", {})
    if isinstance(email_data.get("recipients"), str):
        email_data["recipients"] = [
            item.strip() for item in email_data["recipients"].split(",") if item.strip()
        ]
    data["email"] = email_data
    return AppSettings(**data)

