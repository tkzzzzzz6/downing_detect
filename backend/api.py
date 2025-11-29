"""FastAPI backend service for drowning detection system"""
import sys
import asyncio
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir.parent))

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
import uvicorn

from backend.api import detection, incidents, config, camera
from backend.services.websocket_manager import ws_manager
from backend.services.detection_service import detection_service
from backend.services.camera_service import camera_service
from backend.core.logger import setup_logger
from backend.core.settings import load_settings

# Setup logging
settings = load_settings()
setup_logger(settings.logging)

# Create FastAPI app
app = FastAPI(
    title="Drowning Detection System API",
    description="Backend API for real-time drowning detection system",
    version="1.0.0"
)

# Add CORS middleware to allow frontend to connect
# Allow all origins for development (in production, specify exact origins)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=False,  # Must be False when allow_origins=["*"]
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(detection.router)
app.include_router(incidents.router)
app.include_router(config.router)
app.include_router(camera.router)


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on server shutdown"""
    logger.info("Server shutdown initiated, cleaning up resources...")

    # Stop any active detection sessions
    try:
        if detection_service.current_session and detection_service.current_session.status == "running":
            logger.info("Stopping active detection session...")
            await detection_service.stop_detection()
    except Exception as e:
        logger.warning(f"Error stopping detection session during shutdown: {e}")

    # Clean up camera previews
    try:
        camera_service.cleanup()
    except Exception as e:
        logger.warning(f"Error cleaning up camera service: {e}")

    logger.info("Cleanup complete")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "Drowning Detection System API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "message": "Backend service is running"
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await ws_manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and receive messages from client
            data = await websocket.receive_text()
            # Handle ping/pong or other control messages if needed
            if data == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await ws_manager.disconnect(websocket)


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error": str(exc)
        }
    )


def main():
    """Run the FastAPI application"""
    logger.info("")
    logger.success("=" * 70)
    logger.success("DROWNING DETECTION SYSTEM - BACKEND SERVER".center(70))
    logger.success("=" * 70)
    logger.info("")
    logger.info(f"Server URL       : http://127.0.0.1:8001")
    logger.info(f"API Documentation: http://127.0.0.1:8001/docs")
    logger.info(f"Health Check     : http://127.0.0.1:8001/health")
    logger.info("")
    logger.success("Server is starting...")
    logger.info("Press Ctrl+C to stop the server")
    logger.info("")

    # Use timeout_graceful_shutdown to ensure faster shutdown
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8001,
        log_level="info",
        access_log=True,
        timeout_graceful_shutdown=3  # Wait max 3 seconds for graceful shutdown
    )


if __name__ == "__main__":
    main()
