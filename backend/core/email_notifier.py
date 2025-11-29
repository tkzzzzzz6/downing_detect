import smtplib
from email.message import EmailMessage
from pathlib import Path

from loguru import logger

from .incident_manager import IncidentRecord
from .settings import EmailSettings
from .logger import log_email_sent


class EmailNotifier:
    def __init__(self, config: EmailSettings) -> None:
        self.config = config

    def send_incident(self, incident: IncidentRecord) -> bool:
        if not self.config.enabled:
            logger.info("Email config incomplete; skipping send for incident %s", incident.incident_id)
            return False

        message = self._build_message(incident)
        try:
            if self.config.use_tls and self.config.smtp_port == 465:
                with smtplib.SMTP_SSL(self.config.smtp_server, self.config.smtp_port) as smtp:
                    smtp.login(self.config.username, self.config.password)
                    smtp.send_message(message)
            else:
                with smtplib.SMTP(self.config.smtp_server, self.config.smtp_port) as smtp:
                    if self.config.use_tls:
                        smtp.starttls()
                    smtp.login(self.config.username, self.config.password)
                    smtp.send_message(message)
            # 使用专业的日志
            log_email_sent(self.config.recipients, incident.incident_id)
            return True
        except Exception as exc:  # pragma: no cover - network operations
            logger.error(f"Email sending failed (Incident ID: {incident.incident_id}): {exc}")
            return False

    def _build_message(self, incident: IncidentRecord) -> EmailMessage:
        msg = EmailMessage()
        subject = f"溺水预警 - {incident.camera_id} - {incident.timestamp:.0f}"
        msg["Subject"] = subject
        msg["From"] = self.config.sender
        msg["To"] = ", ".join(self.config.recipients)

        summary = incident.vlm_summary or "VLM 暂不可用，以下为检测到的关键信息。"
        confidence = f"{incident.vlm_confidence:.2f}" if incident.vlm_confidence is not None else "N/A"

        html = f"""
        <h2>溺水预警</h2>
        <p><strong>摄像头：</strong>{incident.camera_id}</p>
        <p><strong>帧编号：</strong>{incident.frame_id}</p>
        <p><strong>重叠比例：</strong>{incident.overlap_ratio:.2f}</p>
        <p><strong>VLM 置信度：</strong>{confidence}</p>
        <p><strong>描述：</strong>{summary}</p>
        <p><strong>BBox：</strong>{incident.bbox}</p>
        <p><strong>截图：</strong>{Path(incident.screenshot_path).name if incident.screenshot_path else "无"}</p>
        """
        msg.set_content("请使用支持 HTML 的客户端查看详细内容。")
        msg.add_alternative(html, subtype="html")

        if incident.screenshot_path:
            screenshot_file = Path(incident.screenshot_path)
            if screenshot_file.exists():
                with open(screenshot_file, "rb") as fh:
                    msg.add_attachment(
                        fh.read(),
                        maintype="image",
                        subtype="png",
                        filename=screenshot_file.name,
                    )
        return msg

