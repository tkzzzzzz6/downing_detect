import pygame
from loguru import logger


class AudioManager:
    def __init__(self, warning_sound_path):
        try:
            pygame.init()
            pygame.mixer.init()
            self.warning_sound_path = warning_sound_path
            pygame.mixer.music.load(self.warning_sound_path)
            logger.info(f"音频管理器初始化成功，警告音文件: {warning_sound_path}")
        except Exception as e:
            logger.error(f"音频管理器初始化失败: {e}")
            raise

    def play_warning(self):
        try:
            pygame.mixer.music.play(-1)  # 循环播放警告音乐
            logger.info("开始播放警告音")
        except Exception as e:
            logger.error(f"播放警告音失败: {e}")

    def stop_warning(self):
        try:
            pygame.mixer.music.stop()
            logger.info("停止播放警告音")
        except Exception as e:
            logger.error(f"停止警告音失败: {e}")

    def cleanup(self):
        try:
            pygame.quit()
            logger.info("音频管理器清理完成")
        except Exception as e:
            logger.error(f"音频管理器清理失败: {e}")