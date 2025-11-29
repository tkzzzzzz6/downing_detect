from pathlib import Path

from loguru import logger
from ultralytics import YOLO


class ModelLoader:
    def __init__(self):
        river_model_path = Path("model/best_seg.pt")
        person_model_path = Path("model/best_detect.pt")
        
        try:
            logger.info(f"加载河流分割模型: {river_model_path}")
            self.model_river = YOLO(str(river_model_path))
            logger.info("河流分割模型加载成功")
        except Exception as e:
            logger.error(f"加载河流分割模型失败: {e}")
            raise
        
        try:
            logger.info(f"加载人员检测模型: {person_model_path}")
            self.model_person = YOLO(str(person_model_path))
            logger.info("人员检测模型加载成功")
        except Exception as e:
            logger.error(f"加载人员检测模型失败: {e}")
            raise

    def get_river_model(self):
        return self.model_river

    def get_person_model(self):
        return self.model_person