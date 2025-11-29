# 这个文件可以为空,或者包含一些包级别的导入

# 例如,你可以在这里导入常用的模块,使它们更容易从包的其他地方访问
from .video_processor import VideoProcessor
from .audio_manager import AudioManager
from .detection_utils import draw_river_mask, draw_person_boxes, draw_warning, draw_info
from .model_loader import ModelLoader

# 你也可以定义 __all__ 变量来控制 from src import * 时导入的内容
__all__ = ['VideoProcessor', 'AudioManager', 'draw_river_mask', 'draw_person_boxes', 'draw_warning', 'draw_info', 'ModelLoader']