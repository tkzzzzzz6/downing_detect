"""日志配置模块，使用 Loguru 进行日志管理"""

import sys
import os
from pathlib import Path
from typing import Optional

from loguru import logger

from .settings import LogSettings, load_settings

# 启用 Windows 终端颜色支持
if sys.platform == "win32":
    os.system("")  # 启用 ANSI 转义序列支持


# 日志级别颜色映射
LEVEL_COLOR_MAP = {
    "TRACE": "dim white",
    "DEBUG": "cyan",
    "INFO": "white",
    "SUCCESS": "bold green",
    "WARNING": "bold yellow",
    "ERROR": "bold red",
    "CRITICAL": "bold white on red",
}


def _console_formatter(record) -> str:
    """专业的控制台日志格式 - 不同级别使用不同颜色"""
    # 简化的模块路径（只显示最后两级）
    module_parts = record["name"].split(".")
    short_module = ".".join(module_parts[-2:]) if len(module_parts) >= 2 else record["name"]

    # 使用简单的格式字符串，让 colorize=True 自动处理颜色
    level_name = record["level"].name

    if level_name in ["ERROR", "CRITICAL"]:
        # 错误日志
        return (
            "[{time:HH:mm:ss.SSS}] <red><bold>{level: <8}</bold></red> "
            "<cyan>{name: <25}</cyan> | <level>{message}</level>\n"
        )
    elif level_name == "WARNING":
        # 警告日志
        return (
            "[{time:HH:mm:ss.SSS}] <yellow><bold>{level: <8}</bold></yellow> "
            "<cyan>{name: <25}</cyan> | <level>{message}</level>\n"
        )
    elif level_name == "SUCCESS":
        # 成功日志
        return (
            "[{time:HH:mm:ss.SSS}] <green><bold>{level: <8}</bold></green> "
            "<cyan>{name: <25}</cyan> | <level>{message}</level>\n"
        )
    else:
        # 普通INFO和DEBUG日志
        return (
            "[{time:HH:mm:ss.SSS}] {level: <8} "
            "<cyan>{name: <25}</cyan> | {message}\n"
        )


FILE_LOG_FORMAT = (
    "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
    "{level: <8} | "
    "{name}:{function}:{line} | "
    "{message}"
)


def setup_logger(config: Optional[LogSettings] = None) -> None:
    """
    配置 Loguru 日志系统
    
    Args:
        config: 日志配置，如果为 None 则从 settings 加载
    """
    if config is None:
        settings = load_settings()
        config = settings.logging
    
    # 移除默认的 handler
    logger.remove()
    
    # 解析日志级别
    level = config.level.upper()
    console_level = (config.console_level or config.level).upper()
    
    # 创建日志目录
    log_dir = Path(config.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # 控制台输出（彩色，等级区分颜色）
    logger.add(
        sys.stderr,
        format=_console_formatter,
        level=console_level,
        colorize=True,
        backtrace=True,
        diagnose=True,
    )
    
    # 文件输出（所有日志，去除颜色编码）
    log_file = log_dir / config.file_pattern
    logger.add(
        str(log_file),
        format=FILE_LOG_FORMAT,
        level=level,
        rotation=config.rotation,
        retention=config.retention,
        compression="zip",
        encoding="utf-8",
        backtrace=True,
        diagnose=True,
    )
    
    # 错误日志单独文件
    error_log_file = log_dir / "error_{time:YYYY-MM-DD}.log"
    logger.add(
        str(error_log_file),
        format=FILE_LOG_FORMAT,
        level="ERROR",
        rotation=config.rotation,
        retention=config.retention,
        compression="zip",
        encoding="utf-8",
        backtrace=True,
        diagnose=True,
    )
    
    logger.info(f"日志系统已初始化 - 日志级别: {level}, 控制台级别: {console_level}, 日志目录: {log_dir}")


def get_logger(name: Optional[str] = None):
    """
    获取 logger 实例

    Args:
        name: logger 名称，通常使用 __name__

    Returns:
        logger 实例
    """
    if name:
        return logger.bind(name=name)
    return logger


# ============================================================================
# 专业日志辅助函数
# ============================================================================

def log_section_header(title: str, char: str = "=", width: int = 70):
    """打印章节标题"""
    logger.info("")
    logger.info(char * width)
    logger.info(f"{title.center(width)}")
    logger.info(char * width)


def log_section_footer(char: str = "=", width: int = 70):
    """打印章节结尾"""
    logger.info(char * width)
    logger.info("")


def log_detection_start(session_id: str, video_source: str, is_webcam: bool):
    """检测开始日志"""
    source_type = "Webcam" if is_webcam else "Video File"
    logger.success("Detection session started")
    logger.info(f"  Session ID    : {session_id}")
    logger.info(f"  Source Type   : {source_type}")
    logger.info(f"  Source        : {video_source}")


def log_detection_stop(session_id: str, frame_count: int, elapsed_time: float):
    """检测停止日志"""
    logger.success("Detection session stopped")
    logger.info(f"  Session ID    : {session_id}")
    logger.info(f"  Frames        : {frame_count:,} frames")
    logger.info(f"  Duration      : {elapsed_time:.2f} seconds")
    if elapsed_time > 0:
        fps = frame_count / elapsed_time
        logger.info(f"  Average FPS   : {fps:.2f}")


from typing import Optional


def log_video_info(fps: float, width: int, height: int, total_frames: Optional[int]):
    """视频信息日志"""
    logger.info("Video Information:")
    logger.info(f"  Resolution    : {width} x {height}")
    logger.info(f"  Frame Rate    : {fps:.2f} FPS")
    if total_frames is not None and total_frames > 0:
        logger.info(f"  Total Frames  : {total_frames:,}")
        duration = total_frames / fps if fps > 0 else 0
        logger.info(f"  Duration      : {duration:.2f} seconds")
    elif total_frames is None:
        logger.info("  Total Frames  : N/A (live stream)")


def log_drowning_alert(frame_id: int, overlap_ratio: float, incident_id: str = None):
    """溺水警报日志"""
    logger.warning("=" * 70)
    logger.warning("DROWNING DANGER DETECTED - IMMEDIATE ATTENTION REQUIRED".center(70))
    logger.warning("=" * 70)
    logger.warning(f"  Frame ID      : {frame_id}")
    logger.warning(f"  Overlap Ratio : {overlap_ratio:.1%}")
    if incident_id:
        logger.warning(f"  Incident ID   : {incident_id}")
    logger.warning("=" * 70)


def log_incident_created(incident_id: str, screenshot_path: str):
    """事件创建日志"""
    logger.success("Incident record created")
    logger.info(f"  Incident ID   : {incident_id}")
    logger.info(f"  Screenshot    : {screenshot_path}")


def log_statistics(stats: dict):
    """统计信息日志"""
    logger.info("Statistics:")
    for key, value in stats.items():
        if isinstance(value, float):
            logger.info(f"  {key:<15} : {value:.2f}")
        elif isinstance(value, int):
            logger.info(f"  {key:<15} : {value:,}")
        else:
            logger.info(f"  {key:<15} : {value}")


def log_vlm_request(provider: str, model: str):
    """VLM请求日志"""
    logger.debug(f"VLM analysis request: {provider}/{model}")


def log_vlm_response(confidence: float, summary: str):
    """VLM响应日志"""
    logger.success(f"VLM analysis completed (confidence: {confidence:.1%})")
    logger.debug(f"  Result: {summary[:100]}...")


def log_email_sent(recipients: list, incident_id: str):
    """邮件发送日志"""
    logger.success("Email notification sent")
    logger.info(f"  Recipients    : {', '.join(recipients)}")
    logger.info(f"  Incident ID   : {incident_id}")
