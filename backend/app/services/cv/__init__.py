"""
Computer Vision PPE Compliance Detection Service Package.
Milestone 2 - Phase 2.2
"""

from app.services.cv.base_detector import (
    BasePPEDetector,
    BoundingBox,
    RawPPEDetection,
    PersonDetection,
    DetectorOutput,
)
from app.services.cv.cv_detector import ComputerVisionPPEDetector
from app.services.cv.mock_detector import MockPPEDetector, PPE_DEMO_SCENARIOS
from app.services.cv.ppe_service import PPEDetectionService, ppe_detection_service

__all__ = [
    "BasePPEDetector",
    "BoundingBox",
    "RawPPEDetection",
    "PersonDetection",
    "DetectorOutput",
    "ComputerVisionPPEDetector",
    "MockPPEDetector",
    "PPE_DEMO_SCENARIOS",
    "PPEDetectionService",
    "ppe_detection_service",
]
