# 溺水检测系统

## 项目简介

本项目是一个基于计算机视觉的溺水检测系统。它能够实时分析视频流,识别水域中的人员,并在检测到潜在溺水危险时发出警告。

## 环境配置

### 依赖项

本项目依赖以下主要库：

| 库名                                     | 版本                   |
|------------------------------------------|------------------------|
| Python                                   | 3.8+                   |
| NumPy                                    | 1.24.4                 |
| OpenCV-Python                            | 4.10.0.84              |
| PyTorch                                  | 2.4.1                  |
| Torchvision                              | 0.19.1                 |
| Ultralytics                              | 8.3.3                  |
| Pygame                                   | 2.6.1                  |
| Pillow                                   | 10.4.0                 |
| Matplotlib                               | 3.7.5                  |
| SciPy                                    | 1.10.1                 |
| Pydantic                                 | 2.9.1                  |
| PyYAML                                   | 6.0.1                  |
| tqdm                                     | 4.66.5                 |

### 安装步骤

1. 克隆仓库:
   ```bash
   git clone https://github.com/your-username/drowning-detection.git
   cd drowning-detection
   ```

2. 创建并激活虚拟环境(推荐):
   ```bash
   python -m venv venv
   source venv/bin/activate  # 在Windows上使用 venv\Scripts\activate
   ```

3. 安装依赖:
   ```bash
   pip install -r requirements.txt
   ```

这将安装项目所需的所有依赖项,并确保版本与开发环境一致。

注意: 如果您在安装过程中遇到任何问题,特别是与CUDA或GPU支持相关的问题,请参考PyTorch官方文档以获取适合您系统的安装说明。

## 使用说明

1. 确保您有适当的视频文件用于检测。

2. 修改 `main.py` 中的 `video_path` 变量,指向您的视频文件:
   ```python
   video_path = "path/to/your/video.mp4"
   ```

3. 运行主程序:
   ```bash
   python main.py
   ```

4. 程序将开始处理视频,并在检测到潜在溺水危险时发出警告。

5. 按 'q' 键退出程序。

## 项目结构

```
DOWNING_DETECT/
│
├── _pycache_/
│   ├── audio_manager.cpython-38.pyc
│   ├── detection_utils.cpython-38.pyc
│   ├── model_loader.cpython-38.pyc
│   ├── video_processor.cpython-38.pyc
│   └── video_processor.cpython-312.pyc
│
├── model/
│   ├── best_detect.pt
│   └── best_seg.pt
│
├── output/
│   └── output_video.mp4
│
├── resource/
│   ├── downing_warning.mp3
│   └── 检测到溺水危险.mp3
│
├── src/
│   ├── _pycache_/
│   ├── __init__.py
│   ├── audio_manager.py
│   ├── detection_utils.py
│   ├── downing_detect_video.py
│   ├── downing_detect_webcam.py
│   ├── model_loader.py
│   └── video_processor.py
│
├── LICENSE
├── README.md
├── main.py
├── requirements.txt
└── train.py
```

这个结构展示了项目的主要组成部分：

- `_pycache_/`: Python 的字节码缓存目录。
- `model/`: 存放模型文件。
- `output/`: 存放输出视频。
- `resource/`: 存放音频资源文件。
- `src/`: 源代码目录，包含项目的主要 Python 模块。
- `LICENSE`: 项目许可证文件。
- `README.md`: 项目说明文档（本文件）。
- `main.py`: 主程序入口。
- `requirements.txt`: 项目依赖列表。
- `train.py`: 模型训练脚本。
