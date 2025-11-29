# 溺水检测系统

## 项目简介

本项目是一个基于计算机视觉的溺水检测系统。它能够实时分析视频流,识别水域中的人员,并在检测到潜在溺水危险时发出警告。

## 项目演示

![Demo GIF](Demo_Video/Demo_01.gif)

演示视频来源: <https://www.bilibili.com/video/BV1JVsxe4EJR/?spm_id_from=333.337.search-card.all.click>

## 环境配置

### 依赖项

本项目依赖以下主要库：

| 库名                | 版本       | 描述                                           |
|:-------------------|:-----------|:----------------------------------------------|
| Python              | 3.8+       | 项目语言                                       |
| NumPy               | 1.24.4     | 科学计算库                                     |
| OpenCV-Python       | 4.10.0.84  | 计算机视觉库                                   |
| PyTorch             | 2.4.1      | 深度学习框架                                   |
| Torchvision         | 0.19.1     | PyTorch的计算机视觉库                          |
| Ultralytics         | 8.3.3      | YOLOv11的实现                           |
| Pygame              | 2.6.1      | 多媒体库，用于音频播放                         |
| Pillow              | 10.4.0     | 图像处理库                                     |
| Matplotlib          | 3.7.5      | 绘图库                                         |
| SciPy               | 1.10.1     | 科学计算库                                     |
| Pydantic            | 2.9.1      | 数据验证和设置管理库                           |
| PyYAML              | 6.0.1      | YAML解析器和生成器                             |
| tqdm                | 4.66.5     | 进度条库                                       |
| httpx               | 0.27.2     | VLM API 调用的 HTTP 客户端                      |
| prometheus-client   | 0.19.0     | 指标采集/导出                                  |

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

## 配置与使用说明

1. **准备配置文件**  
   将 `config/settings.example.yaml` 复制为 `config/settings.yaml`, 根据实际环境填写：
   - `email`：SMTP 服务端、账号、收件人列表（支持多个）。
   - `vlm`：选择 `provider`（openai/qwen/moonshot/ollama）、模型名、API Key/本地端点、提示词等。
   - `incident_output_dir`：事件截图的输出目录。
   > 也可通过环境变量覆盖同名字段,例如 `VLM_PROVIDER=qwen`、`EMAIL_RECIPIENTS=a@x.com,b@y.com`。

2. **准备检测素材**：确保有视频文件或摄像头可供检测。

3. **运行主程序**：

   ```bash
   python main.py
   ```

   根据提示选择 1（视频文件）或 2（摄像头）。程序会在 `output/` 下输出处理后的视频，并在 `config` 中启用 VLM/邮件时自动发送包含截图与描述的邮件。

4. 按 'q' 键退出视频窗口。

## 项目结构

```text
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
│   ├── output_video.mp4
│   └── incidents/
│       └── *.png
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
│   ├── email_notifier.py
│   ├── incident_manager.py
│   ├── model_loader.py
│   ├── settings.py
│   ├── video_processor.py
│   ├── vlm_client.py
│   └── vlm_worker.py
│
├── config/
│   └── settings.example.yaml
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
