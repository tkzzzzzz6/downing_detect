from ultralytics import YOLO

class ModelLoader:
    def __init__(self):
        self.model_river = YOLO(r"model/best_seg.pt")
        self.model_person = YOLO(r"model/best_detect.pt")

    def get_river_model(self):
        return self.model_river

    def get_person_model(self):
        return self.model_person