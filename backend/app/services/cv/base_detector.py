"""
Base Computer Vision PPE Detector Interface
===========================================
Defines the abstract contract for all Computer Vision PPE detectors.
Enables pluggable models (OpenCV, YOLO, TorchVision, Cloud Vision, Test Mocks)
without modifying orchestrators, SafetyAgent, or API layers.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import uuid


@dataclass
class BoundingBox:
    x: float
    y: float
    width: float
    height: float

    def to_dict(self) -> Dict[str, float]:
        return {
            "x": round(self.x, 2),
            "y": round(self.y, 2),
            "width": round(self.width, 2),
            "height": round(self.height, 2),
        }


@dataclass
class RawPPEDetection:
    detection_id: str
    ppe_class: str                    # "HARD_HAT", "SAFETY_VEST", "SAFETY_GOGGLES"
    confidence: float                 # Model prediction confidence [0.0 - 1.0]
    bounding_box: BoundingBox
    status: str = "DETECTED"          # "DETECTED" | "LOW_CONFIDENCE" | "MISSING"
    is_compliant: bool = True
    person_id: Optional[str] = None
    detection_source: str = "COMPUTER_VISION"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "detection_id": self.detection_id,
            "ppe_class": self.ppe_class,
            "confidence": round(self.confidence, 4),
            "bounding_box": self.bounding_box.to_dict(),
            "status": self.status,
            "is_compliant": self.is_compliant,
            "person_id": self.person_id,
            "detection_source": self.detection_source,
        }


@dataclass
class PersonDetection:
    person_id: str
    bounding_box: BoundingBox
    confidence: float
    detected_ppe: List[RawPPEDetection] = field(default_factory=list)
    missing_ppe: List[str] = field(default_factory=list)
    is_compliant: bool = False
    worker_id: Optional[str] = None
    worker_name: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "person_id": self.person_id,
            "bounding_box": self.bounding_box.to_dict(),
            "confidence": round(self.confidence, 4),
            "detected_ppe": [d.to_dict() for d in self.detected_ppe],
            "missing_ppe": self.missing_ppe,
            "is_compliant": self.is_compliant,
            "worker_id": self.worker_id,
            "worker_name": self.worker_name,
        }


@dataclass
class DetectorOutput:
    image_width: int
    image_height: int
    persons: List[PersonDetection]
    detections: List[RawPPEDetection]
    model_name: str
    detection_source: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "image_width": self.image_width,
            "image_height": self.image_height,
            "persons": [p.to_dict() for p in self.persons],
            "detections": [d.to_dict() for d in self.detections],
            "model_name": self.model_name,
            "detection_source": self.detection_source,
        }


class BasePPEDetector(ABC):
    """
    Abstract interface for Computer Vision PPE object detection.
    """

    @property
    @abstractmethod
    def model_name(self) -> str:
        pass

    @property
    @abstractmethod
    def detection_source(self) -> str:
        pass

    @abstractmethod
    def detect(self, image_path: str, context: Optional[Dict[str, Any]] = None) -> DetectorOutput:
        """
        Execute PPE detection on the given image file.
        Returns DetectorOutput with identified persons and PPE bounding boxes.
        """
        pass
