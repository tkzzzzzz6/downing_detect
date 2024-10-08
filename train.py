from ultralytics import YOLO
import multiprocessing

def main():
    # 使用支持实例分割的模型
    model = YOLO("yolo11n.pt")  # 使用YOLOv8的分割模型
    data_path = r"D:\yolo\ultralytics\downing_test_1.v13i.yolov11\data.yaml"
    train_result = model.train(
        data=data_path, 
        epochs=100,
        imgsz=640,
        device=0,
        patience=50,
        batch=16,
        lr0=0.01,
        lrf=0.01,
        augment=True,
        val=True,
        # task='segment'  # 设置任务为分割
    )
    
    # 保存训练结果
    print(f"Best mAP: {train_result.best_fitness}")
    model.export()  # 导出最佳模型

if __name__ == '__main__':
    multiprocessing.freeze_support()
    main()