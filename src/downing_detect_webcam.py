from ultralytics import YOLO
import cv2
import numpy as np
import pygame
import time

# 初始化pygame
pygame.init()
pygame.mixer.init()

# 加载两个模型
model_river = YOLO(r"D:\yolo\ultralytics\runs\segment\train3\weights\best.pt")
model_person = YOLO(r"D:\yolo\ultralytics\yolo11s.pt")

# 打开手机webcam虚拟摄像头
cap = cv2.VideoCapture(0)  # 使用索引0表示默认摄像头，如果不是默认摄像头，可能需要尝试其他索引

# 获取视频的帧率和尺寸
fps = int(cap.get(cv2.CAP_PROP_FPS))
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

# 创建视频写入器
output_path = "output_video.mp4"  # 输出视频的文件名
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

# 警告音频路径
warning_sound_path = r"D:\yolo\ultralytics\resource\检测到溺水危险.mp3"

# 加载警告音频
pygame.mixer.music.load(warning_sound_path)

# 初始化变量
warning_active = False
last_detection_time = 0
warning_start_time = 0
warning_duration = 15  # 警告持续时间（秒）
detection_window = 30  # 检测窗口时间（秒）

while True:
    # 读取视频帧
    ret, frame = cap.read()
    if not ret:
        break

    current_time = time.time()

    # 使用两个模型进行目标检测、跟踪和分割
    results_river = model_river.track(source=frame, show=False, tracker="bytetrack.yaml")
    results_person = model_person.track(source=frame, show=False, tracker="bytetrack.yaml")

    # 在原始帧上绘制检测结果
    annotated_frame = frame.copy()
    
    # 创建河流掩码
    river_mask = np.zeros((height, width), dtype=np.uint8)
    
    # 处理河流检测结果
    for r in results_river:
        masks = r.masks
        if masks is not None:
            for mask in masks:
                seg = mask.xy[0].astype(np.int32)
                if len(seg) > 0:  # 检查分割结果是否为空
                    # 填充河流掩码
                    cv2.fillPoly(river_mask, [seg], 255)
                    
                    # 使用alpha混合来填充分割区域
                    alpha = 0.4
                    overlay = annotated_frame.copy()
                    cv2.fillPoly(overlay, [seg], (0, 0, 255))
                    cv2.addWeighted(overlay, alpha, annotated_frame, 1 - alpha, 0, annotated_frame)
                    
                    # 绘制轮廓
                    cv2.polylines(annotated_frame, [seg], True, (255, 255, 255), 2)
                    
                    # 添加标签
                    label = "River"
                    # 计算边界框
                    x, y, w, h = cv2.boundingRect(seg)
                    text_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.9, 2)[0]
                    text_x = x
                    text_y = y + text_size[1] + 10
                    cv2.rectangle(annotated_frame, (text_x, text_y - text_size[1] - 10), (text_x + text_size[0], text_y), (255, 255, 255), -1)
                    cv2.putText(annotated_frame, label, (text_x, text_y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)

    # 处理人物检测结果
    person_detected = False
    for r in results_person:
        boxes = r.boxes
        if boxes is not None:
            for box in boxes:
                if int(box.cls) == 0:  # 假设 0 是 'person'
                    b = box.xyxy[0].cpu().numpy().astype(int)
                    track_id = box.id.int().cpu().item() if box.id is not None else None
                    label = f"Person {track_id}" if track_id is not None else "Person"
                    
                    # 创建人物掩码
                    person_mask = np.zeros((height, width), dtype=np.uint8)
                    cv2.rectangle(person_mask, (b[0], b[1]), (b[2], b[3]), 255, -1)
                    
                    # 计算重叠区域
                    overlap = cv2.bitwise_and(river_mask, person_mask)
                    overlap_ratio = np.sum(overlap) / np.sum(person_mask) if np.sum(person_mask) > 0 else 0

                    # 检查重叠比例
                    if overlap_ratio > 0.90:
                        person_detected = True
                        last_detection_time = current_time
                    
                    # 绘制边界框
                    cv2.rectangle(annotated_frame, (b[0], b[1]), (b[2], b[3]), (0, 255, 0), 2)
                    
                    # 添加标签
                    text_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.9, 2)[0]
                    cv2.rectangle(annotated_frame, (b[0], b[1] - text_size[1] - 10), (b[0] + text_size[0], b[1]), (0, 255, 0), -1)
                    cv2.putText(annotated_frame, label, (b[0], b[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)

    # 处理警告逻辑
    if person_detected and not warning_active:
        warning_active = True
        warning_start_time = current_time
        pygame.mixer.music.play(-1)  # 循环播放警告音乐

    if warning_active:
        # 在检测窗口显示警告信息
        cv2.putText(annotated_frame, "WARNING: Person in danger!", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        # 检查是否需要停止警告
        if current_time - last_detection_time > detection_window:
            warning_active = False
            pygame.mixer.music.stop()
    
    # 检查是否需要停止警告（即使仍在检测到危险）
    if warning_active and current_time - warning_start_time > warning_duration:
        warning_active = False
        pygame.mixer.music.stop()

    # 将处理后的帧写入输出视频
    out.write(annotated_frame)

    # 显示结果（可选，如果不需要实时显示可以注释掉）
    cv2.imshow('Detection Results', annotated_frame)

    # 按'q'键退出
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# 释放资源
cap.release()
out.release()
cv2.destroyAllWindows()
pygame.quit()
