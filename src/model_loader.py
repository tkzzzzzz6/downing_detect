from ultralytics import YOLO

class ModelLoader:
    def __init__(self):
        self.model_river = YOLO(r"D:\yolo\ultralytics\runs\segment\train16\weights\best.pt")
        self.model_person = YOLO(r"D:\yolo\ultralytics\runs\detect\train40\weights\best.pt")

    def get_river_model(self):
        return self.model_river

    def get_person_model(self):
        return self.model_person