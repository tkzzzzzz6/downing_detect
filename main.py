from src.video_processor import VideoProcessor

def main():
    video_path = r"C:\Users\tk\Videos\序列 04.mp4"
    output_path = "output/output_video.mp4"
    warning_sound_path = "resource/检测到溺水危险.mp3"
    
    processor = VideoProcessor(video_path, output_path, warning_sound_path)
    processor.process_video()

if __name__ == "__main__":
    main()