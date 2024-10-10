import cv2
import time
from src.model_loader import ModelLoader
from src.detection_utils import draw_river_mask, draw_person_boxes, draw_warning, draw_info, calculate_overlap_ratio
from tqdm import tqdm

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
        self.last_print_time = 0
        self.print_interval = 1  # 每秒打印一次警告信息
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT)) if not is_webcam else None

    def process_video(self):
        frame_count = 0
        pbar = tqdm(total=self.total_frames, desc="Processing video", unit="frames") if self.total_frames else None
        
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
                    self.print_warning(self.info_message)

            if self.warning_active:
                draw_warning(annotated_frame)

                if current_time - self.last_print_time >= self.print_interval:
                    self.print_warning(self.info_message)
                    self.last_print_time = current_time

                if current_time - self.last_detection_time > self.detection_window:
                    self.warning_active = False
                    self.info_message = "Warning cleared: Detection window time exceeded"
                    self.print_warning_cleared(self.info_message)
            
            if self.warning_active and current_time - self.warning_start_time > self.warning_duration:
                self.warning_active = False
                self.info_message = "Warning cleared: Warning duration exceeded"
                self.print_warning_cleared(self.info_message)

            draw_info(annotated_frame, self.info_message)

            self.out.write(annotated_frame)

            frame_count += 1
            if pbar:
                pbar.update(1)

        if pbar:
            pbar.close()
        self.cleanup()

    def print_warning(self, message):
                # 打印多行警告解除信息，使其更加显眼
        print("\n" + "=" * 50)
        for _ in range(10):
            print(f"\033[91m{message}\033[0m")  # 黄色文字输出警告解除信息
        print("=" * 50 + "\n")


    def print_warning_cleared(self, message):
        # 打印多行警告解除信息，使其更加显眼
        print("\n" + "=" * 50)
        for _ in range(50):
            print(f"\033[93m{message}\033[0m")  # 黄色文字输出警告解除信息
        print("=" * 50 + "\n")

    def cleanup(self):
        self.cap.release()
        self.out.release()