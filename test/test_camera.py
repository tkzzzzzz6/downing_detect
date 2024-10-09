import cv2
import time

def test_camera():
    print("尝试打开摄像头...")
    cap = cv2.VideoCapture(0)  # 尝试打开默认摄像头
    
    if not cap.isOpened():
        print("无法打开摄像头。尝试其他摄像头索引...")
        for i in range(1, 10):  # 尝试其他摄像头索引
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                print(f"成功打开摄像头 {i}")
                break
        else:
            print("无法找到可用的摄像头")
            return

    while True:
        ret, frame = cap.read()
        if not ret:
            print("无法获取画面")
            time.sleep(1)  # 等待1秒后重试
            continue

        # 检查帧是否为空
        if frame is None or frame.size == 0:
            print("获取到空帧")
            continue

        # 显示画面
        cv2.imshow('Camera Test', frame)

        # 按'q'键退出
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # 释放摄像头资源
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    test_camera()