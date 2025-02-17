from src.video_processor import VideoProcessor
import os

def main():
    while True:
        choice = input("请选择检测模式:\n1. 视频文件检测\n2. 虚拟摄像头检测\n请输入选项 (1 或 2): ")
        
        if choice == '1':
            video_path = input("请输入需要检测的视频文件路径: ")
            if not os.path.exists(video_path):
                print("错误: 指定的视频文件不存在。请检查路径是否正确。")
                continue
            
            output_path = "output/output_video.mp4"
            processor = VideoProcessor(video_path, output_path)
            processor.process_video()
            print("视频处理完成。输出文件保存在:", output_path)
            break
        
        elif choice == '2':
            print("警告: 在无图形界面环境中，虚拟摄像头检测可能无法正常工作。")
            webcam_output_path = "output/webcam_output.mp4"
            webcam_processor = VideoProcessor(0, webcam_output_path, is_webcam=True)
            webcam_processor.process_video()
            print("视频处理完成。输出文件保存在:", webcam_output_path)
            break
        
        else:
            print("无效的选项,请重新输入。")

if __name__ == "__main__":
    main()