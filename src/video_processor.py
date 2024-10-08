import cv2
import time
from src.model_loader import ModelLoader
from src.detection_utils import draw_river_mask, draw_person_boxes, draw_warning, draw_info
from src.audio_manager import AudioManager

class VideoProcessor:
    def __init__(self, video_path, output_path, warning_sound_path):
        self.video_path = video_path
        self.output_path = output_path
        self.cap = cv2.VideoCapture(video_path)
        self.fps = int(self.cap.get(cv2.CAP_PROP_FPS))
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        self.out = cv2.VideoWriter(output_path, fourcc, self.fps, (self.width, self.height))
        
        self.model_loader = ModelLoader()
        self.audio_manager = AudioManager(warning_sound_path)
        
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
                break

            current_time = time.time()

            results_river = self.model_loader.get_river_model().track(source=frame, show=False, tracker="bytetrack.yaml")
            results_person = self.model_loader.get_person_model().track(source=frame, show=False, tracker="bytetrack.yaml")

            annotated_frame = frame.copy()
            
            river_mask = draw_river_mask(annotated_frame, results_river[0].masks)
            person_detected, overlap_ratio = draw_person_boxes(annotated_frame, results_person[0].boxes, river_mask)

            if person_detected:
                self.last_detection_time = current_time
                if not self.warning_active:
                    self.warning_active = True
                    self.warning_start_time = current_time
                    self.audio_manager.play_warning()
                    self.info_message = f"Warning: Drowning danger detected! Overlap ratio: {overlap_ratio:.2f}"

            if self.warning_active:
                draw_warning(annotated_frame)

                if current_time - self.last_detection_time > self.detection_window:
                    self.warning_active = False
                    self.audio_manager.stop_warning()
                    self.info_message = "Warning deactivated: Exceeded detection window time"
            
            if self.warning_active and current_time - self.warning_start_time > self.warning_duration:
                self.warning_active = False
                self.audio_manager.stop_warning()
                self.info_message = "Warning deactivated: Exceeded warning duration"

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
        self.audio_manager.cleanup()