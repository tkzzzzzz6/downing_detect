#!/usr/bin/env python3
"""
测试所有导入是否正常工作
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("🧪 测试后端模块导入...")

try:
    print("\n1. 测试 backend.models...")
    from backend.models import DetectionStartRequest, DetectionStatusResponse
    print("   ✅ backend.models")
except Exception as e:
    print(f"   ❌ backend.models: {e}")

try:
    print("\n2. 测试 backend.core...")
    from backend.core.video_processor import VideoProcessor
    from backend.core.incident_manager import IncidentManager
    from backend.core.model_loader import ModelLoader
    from backend.core.settings import load_settings
    print("   ✅ backend.core")
except Exception as e:
    print(f"   ❌ backend.core: {e}")

try:
    print("\n3. 测试 backend.services...")
    from backend.services.detection_service import detection_service
    from backend.services.incident_service import incident_service
    from backend.services.websocket_manager import ws_manager
    print("   ✅ backend.services")
except Exception as e:
    print(f"   ❌ backend.services: {e}")

try:
    print("\n4. 测试 backend.api...")
    from backend.api import detection, incidents, config
    print("   ✅ backend.api")
except Exception as e:
    print(f"   ❌ backend.api: {e}")

try:
    print("\n5. 测试 FastAPI app...")
    import backend.api as api_module
    print("   ✅ FastAPI app")
except Exception as e:
    print(f"   ❌ FastAPI app: {e}")

print("\n" + "="*60)
print("✅ 所有导入测试完成！")
print("="*60)
print("\n现在可以尝试启动后端：")
print("  uv run backend/api.py")
