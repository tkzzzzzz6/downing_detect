#!/usr/bin/env python3
"""
环境检查脚本 - 验证溺水检测系统的依赖和配置

使用方法:
    uv run check_env.py
"""

import sys
from pathlib import Path


def check_python_version():
    """检查 Python 版本"""
    print("🐍 检查 Python 版本...")
    version = sys.version_info
    if version.major == 3 and version.minor >= 8:
        print(f"   ✅ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"   ❌ Python 版本过低: {version.major}.{version.minor}.{version.micro}")
        print(f"   需要 Python 3.8 或更高版本")
        return False


def check_imports():
    """检查关键依赖是否可以导入"""
    print("\n📦 检查依赖包...")
    packages = {
        "torch": "PyTorch",
        "cv2": "OpenCV",
        "ultralytics": "Ultralytics (YOLO)",
        "fastapi": "FastAPI",
        "pydantic": "Pydantic",
        "loguru": "Loguru",
    }

    all_ok = True
    for module, name in packages.items():
        try:
            __import__(module)
            print(f"   ✅ {name}")
        except ImportError:
            print(f"   ❌ {name} - 未安装")
            all_ok = False

    return all_ok


def check_models():
    """检查模型文件"""
    print("\n🤖 检查模型文件...")
    model_dir = Path("model")
    models = {
        "best_seg.pt": "河流分割模型",
        "best_detect.pt": "人员检测模型",
    }

    all_ok = True
    for filename, description in models.items():
        filepath = model_dir / filename
        if filepath.exists():
            size = filepath.stat().st_size / (1024 * 1024)  # MB
            print(f"   ✅ {description} ({size:.1f} MB)")
        else:
            print(f"   ❌ {description} - 文件不存在: {filepath}")
            all_ok = False

    return all_ok


def check_config():
    """检查配置文件"""
    print("\n⚙️  检查配置文件...")
    config_file = Path("config/settings.yaml")
    config_example = Path("config/settings.example.yaml")

    if config_file.exists():
        print(f"   ✅ settings.yaml 存在")
        return True
    elif config_example.exists():
        print(f"   ⚠️  settings.yaml 不存在，但示例文件存在")
        print(f"   建议运行: cp {config_example} {config_file}")
        return False
    else:
        print(f"   ❌ 配置文件缺失")
        return False


def check_directories():
    """检查必要的目录"""
    print("\n📁 检查目录结构...")
    directories = {
        "backend": "后端目录",
        "backend/api": "API 路由目录",
        "backend/services": "服务层目录",
        "backend/core": "核心代码目录",
        "frontend": "前端目录",
        "model": "模型目录",
        "config": "配置目录",
        "output": "输出目录",
    }

    all_ok = True
    for dir_path, description in directories.items():
        path = Path(dir_path)
        if path.exists() and path.is_dir():
            print(f"   ✅ {description}")
        else:
            print(f"   ❌ {description} - 目录不存在: {dir_path}")
            all_ok = False

    # 自动创建 output 目录
    Path("output/incidents").mkdir(parents=True, exist_ok=True)
    Path("logs").mkdir(exist_ok=True)

    return all_ok


def check_gpu():
    """检查 GPU 可用性"""
    print("\n🎮 检查 GPU...")
    try:
        import torch
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            gpu_count = torch.cuda.device_count()
            print(f"   ✅ CUDA 可用")
            print(f"   GPU: {gpu_name}")
            print(f"   设备数量: {gpu_count}")
            return True
        else:
            print(f"   ⚠️  CUDA 不可用，将使用 CPU")
            print(f"   如需 GPU 加速，请安装 CUDA 版本的 PyTorch")
            return False
    except Exception as e:
        print(f"   ❌ 检查 GPU 时出错: {e}")
        return False


def main():
    """主函数"""
    print("=" * 60)
    print("🔍 溺水检测系统 - 环境检查")
    print("=" * 60)

    checks = {
        "Python 版本": check_python_version(),
        "依赖包": check_imports(),
        "模型文件": check_models(),
        "配置文件": check_config(),
        "目录结构": check_directories(),
        "GPU": check_gpu(),
    }

    print("\n" + "=" * 60)
    print("📊 检查结果汇总")
    print("=" * 60)

    for name, passed in checks.items():
        status = "✅" if passed else "❌"
        print(f"{status} {name}")

    all_passed = all(checks.values())

    if all_passed:
        print("\n🎉 所有检查通过！环境配置正确。")
        print("\n可以开始使用了：")
        print("  - CLI 模式: uv run main.py")
        print("  - Web 后端: uv run backend/api.py")
        print("  - Web 前端: cd frontend && npm start")
        return 0
    else:
        print("\n⚠️  部分检查未通过，请根据上述提示修复。")
        print("\n常见解决方案：")
        print("  - 安装依赖: uv sync")
        print("  - 创建配置: cp config/settings.example.yaml config/settings.yaml")
        print("  - 查看文档: cat QUICKSTART.md")
        return 1


if __name__ == "__main__":
    sys.exit(main())
