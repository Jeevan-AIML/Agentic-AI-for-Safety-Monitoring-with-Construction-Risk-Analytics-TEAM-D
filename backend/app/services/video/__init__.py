"""
Video Surveillance Service Module — Milestone 3 Phase 3.1
"""

from app.services.video.providers import (
    BaseVideoStreamProvider,
    DemoVideoProvider,
    LocalVideoProvider,
    FutureRTSPProvider,
)
from app.services.video.person_detector import (
    BasePersonDetector,
    DemoPersonDetector,
    CVPersonDetector,
)
from app.services.video.video_pipeline import VideoAnalysisPipeline
from app.services.video.demo_scenarios import VIDEO_DEMO_SCENARIOS
from app.services.video.video_service import VideoSurveillanceService, video_service

__all__ = [
    "BaseVideoStreamProvider",
    "DemoVideoProvider",
    "LocalVideoProvider",
    "FutureRTSPProvider",
    "BasePersonDetector",
    "DemoPersonDetector",
    "CVPersonDetector",
    "VideoAnalysisPipeline",
    "VIDEO_DEMO_SCENARIOS",
    "VideoSurveillanceService",
    "video_service",
]
