import cv2
import time
from src.model_loader import ModelLoader
from src.detection_utils import draw_river_mask, draw_person_boxes, draw_warning, draw_info, calculate_overlap_ratio

class VideoProcessor:
    def __init__(self, video_source, output_path, is_webcam=False):
        self.video_source = video_source
        self.output_path = output_path
        self.is_webcam = is_webcam
        
        if self.is_webcam:
            self.cap = cv2.VideoCapture(0)
        else:
            self.cap = cv2.VideoCapture(video_source)
        
        self.fps = int(self.cap.get(cv2.CAP_PROP_FPS))
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        self.out = cv2.VideoWriter(output_path, fourcc, self.fps, (self.width, self.height))
        
        self.model_loader = ModelLoader()
        
        self.warning_active = False
        self.last_detection_time = 0
        self.warning_start_time = 0
        self.warning_duration = 15
        self.detection_window = 30
        self.info_message = ""

    def process_video(self):
        while True:
            ret, frame = self.cap.read()
            if not ret:
                if self.is_webcam:
                    continue
                else:
                    break

            current_time = time.time()

            results_river = self.model_loader.get_river_model().track(source=frame, show=False, tracker="bytetrack.yaml")
            results_person = self.model_loader.get_person_model().track(source=frame, show=False, tracker="bytetrack.yaml")

            annotated_frame = frame.copy()
            
            river_mask = draw_river_mask(annotated_frame, results_river[0].masks if results_river[0].masks is not None else None)
            person_detected, person_masks = draw_person_boxes(annotated_frame, 
                                                              results_person[0].boxes if results_person[0].boxes is not None else None, 
                                                              river_mask)

            max_overlap_ratio = 0
            if person_detected and person_masks:
                for person_mask in person_masks:
                    overlap_ratio = calculate_overlap_ratio(person_mask, river_mask)
                    max_overlap_ratio = max(max_overlap_ratio, overlap_ratio)

            if max_overlap_ratio > 0.90:
                self.last_detection_time = current_time
                if not self.warning_active:
                    self.warning_active = True
                    self.warning_start_time = current_time
                    self.info_message = f"Warning: Drowning danger detected! Overlap ratio: {max_overlap_ratio:.2f}"

            if self.warning_active:
                draw_warning(annotated_frame)

                if current_time - self.last_detection_time > self.detection_window:
                    self.warning_active = False
                    self.info_message = "Warning cleared: Detection window time exceeded"
            
            if self.warning_active and current_time - self.warning_start_time > self.warning_duration:
                self.warning_active = False
                self.info_message = "Warning cleared: Warning duration exceeded"

            draw_info(annotated_frame, self.info_message)

            self.out.write(annotated_frame)

            cv2.imshow('Detection Results', annotated_frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        self.cleanup()

    def cleanup(self):
        self.cap.release()
        self.out.release()
        cv2.destroyAllWindows()