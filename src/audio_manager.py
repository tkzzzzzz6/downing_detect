import pygame

class AudioManager:
    def __init__(self, warning_sound_path):
        pygame.init()
        pygame.mixer.init()
        self.warning_sound_path = warning_sound_path
        pygame.mixer.music.load(self.warning_sound_path)

    def play_warning(self):
        pygame.mixer.music.play(-1)  # 循环播放警告音乐

    def stop_warning(self):
        pygame.mixer.music.stop()

    def cleanup(self):
        pygame.quit()