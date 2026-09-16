"""
Person Detection Abstraction & Implementations — Milestone 3 Phase 3.1
======================================================================
Defines BasePersonDetector abstraction with:
- DemoPersonDetector (deterministic simulation detector with explicit labeling)
- CVPersonDetector (OpenCV HOG / Cascade based detector)
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import uuid

from app.services.cv.base_detector import BoundingBox, PersonDetection

try:
    import cv2
    import numpy as np
    OPENCV_AVAILABLE = True
except ImportError:
    cv2 = None
    np = None
    OPENCV_AVAILABLE = False


class BasePersonDetector(ABC):
    """Abstract interface for video frame person detection."""

    @property
    @abstractmethod
    def detector_name(self) -> str:
        pass

    @property
    @abstractmethod
    def detection_source(self) -> str:
        """Returns COMPUTER_VISION or DEMO / SIMULATION"""
        pass

    @property
    @abstractmethod
    def is_simulation(self) -> bool:
        pass

    @abstractmethod
    def detect_persons(
        self,
        frame_payload: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Detect persons in the given frame.
        Returns a list of dictionaries with keys:
          - person_id: str
          - worker_id: Optional[str]
          - worker_name: Optional[str]
          - bounding_box: BoundingBox / Dict
          - confidence: float
          - timestamp: datetime
          - detection_source: str
          - is_simulation: bool
        """
        pass


class DemoPersonDetector(BasePersonDetector):
    """
    Deterministic simulated person detector for demo scenarios and testing.
    Outputs reproducible person bounding boxes and confidence scores.
    Explicitly labeled: DEMO / SIMULATION.
    """

    @property
    def detector_name(self) -> str:
        return "Deterministic-Demo-Person-Detector-v1.0"

    @property
    def detection_source(self) -> str:
        return "DEMO / SIMULATION"

    @property
    def is_simulation(self) -> bool:
        return True

    def detect_persons(
        self,
        frame_payload: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        context = context or {}
        scenario_id = context.get("scenario_id") or frame_payload.get("scenario_id") or 1
        now = frame_payload.get("timestamp") or datetime.now(timezone.utc)

        persons = []

        # Scenario 1: Safe Site — 2 fully compliant workers in safe area
        if scenario_id == 1:
            persons.append({
                "person_id": "PERSON_01",
                "worker_id": context.get("worker_id") or "worker_01",
                "worker_name": "Marcus Vance",
                "role": "operator",
                "bounding_box": BoundingBox(x=120.0, y=180.0, width=95.0, height=210.0).to_dict(),
                "confidence": 0.94,
                "timestamp": now,
                "detection_source": self.detection_source,
                "is_simulation": True,
                "current_zone": "Safe Laydown Area",
                "is_high_risk_zone": False,
                "simulated_ppe": ["HARD_HAT", "SAFETY_VEST", "SAFETY_GOGGLES"],
            })
            persons.append({
                "person_id": "PERSON_02",
                "worker_id": "worker_02",
                "worker_name": "Elena Rostova",
                "role": "general_worker",
                "bounding_box": BoundingBox(x=340.0, y=200.0, width=90.0, height=200.0).to_dict(),
                "confidence": 0.91,
                "timestamp": now,
                "detection_source": self.detection_source,
                "is_simulation": True,
                "current_zone": "Safe Laydown Area",
                "is_high_risk_zone": False,
                "simulated_ppe": ["HARD_HAT", "SAFETY_VEST", "SAFETY_GOGGLES"],
            })

        # Scenario 2: PPE Violation — Worker missing hard hat in active zone
        elif scenario_id == 2:
            persons.append({
                "person_id": "PERSON_01",
                "worker_id": context.get("worker_id") or "worker_01",
                "worker_name": "Marcus Vance",
                "role": "general_worker",
                "bounding_box": BoundingBox(x=220.0, y=160.0, width=105.0, height=225.0).to_dict(),
                "confidence": 0.89,
                "timestamp": now,
                "detection_source": self.detection_source,
                "is_simulation": True,
                "current_zone": "Active Work Sector",
                "is_high_risk_zone": False,
                "simulated_ppe": ["SAFETY_VEST"],  # Missing HARD_HAT
            })

        # Scenario 3: High-Risk Zone Entry — Worker inside Excavation / Restricted zone
        elif scenario_id == 3:
            persons.append({
                "person_id": "PERSON_01",
                "worker_id": context.get("worker_id") or "worker_01",
                "worker_name": "Marcus Vance",
                "role": "technician",
                "bounding_box": BoundingBox(x=550.0, y=310.0, width=110.0, height=230.0).to_dict(),
                "confidence": 0.92,
                "timestamp": now,
                "detection_source": self.detection_source,
                "is_simulation": True,
                "current_zone": "Excavation Zone",
                "is_high_risk_zone": True,
                "simulated_ppe": ["HARD_HAT", "SAFETY_VEST"],
            })

        # Scenario 4: Heavy Equipment Proximity — Non-operator near operating excavator
        elif scenario_id == 4:
            persons.append({
                "person_id": "PERSON_01",
                "worker_id": context.get("worker_id") or "worker_01",
                "worker_name": "Marcus Vance",
                "role": "general_worker",
                "bounding_box": BoundingBox(x=680.0, y=280.0, width=115.0, height=240.0).to_dict(),
                "confidence": 0.95,
                "timestamp": now,
                "detection_source": self.detection_source,
                "is_simulation": True,
                "current_zone": "Heavy Equipment Zone",
                "is_high_risk_zone": True,
                "nearby_equipment": ["CAT 320 Hydraulic Excavator (Operating)"],
                "simulated_ppe": ["HARD_HAT", "SAFETY_VEST"],
            })

        # Scenario 5: Multiple Safety Violations — Missing PPE, high risk zone & equipment proximity
        elif scenario_id == 5:
            persons.append({
                "person_id": "PERSON_01",
                "worker_id": context.get("worker_id") or "worker_01",
                "worker_name": "Marcus Vance",
                "role": "general_worker",
                "bounding_box": BoundingBox(x=720.0, y=290.0, width=120.0, height=245.0).to_dict(),
                "confidence": 0.93,
                "timestamp": now,
                "detection_source": self.detection_source,
                "is_simulation": True,
                "current_zone": "Excavation Zone",
                "is_high_risk_zone": True,
                "nearby_equipment": ["Komatsu PC210 Excavator (Operating)"],
                "nearby_hazards": ["Unguarded Excavation Trench (Depth 3.5m)"],
                "simulated_ppe": [],  # Missing ALL PPE (no hard hat, no vest)
            })

        # Fallback default
        else:
            persons.append({
                "person_id": "PERSON_DEFAULT",
                "worker_id": context.get("worker_id") or "worker_default",
                "worker_name": "Field Personnel",
                "role": "general_worker",
                "bounding_box": BoundingBox(x=150.0, y=150.0, width=100.0, height=220.0).to_dict(),
                "confidence": 0.88,
                "timestamp": now,
                "detection_source": self.detection_source,
                "is_simulation": True,
                "current_zone": "Safe Laydown Area",
                "is_high_risk_zone": False,
                "simulated_ppe": ["HARD_HAT", "SAFETY_VEST"],
            })

        return persons


class CVPersonDetector(BasePersonDetector):
    """
    OpenCV-based Person Detector using HOG descriptor + SVM.
    Applies real Computer Vision inference on ingested video frames.
    Explicitly labeled: COMPUTER_VISION.
    """

    def __init__(self):
        self._hog = None
        if OPENCV_AVAILABLE:
            try:
                self._hog = cv2.HOGDescriptor()
                self._hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
            except Exception:
                self._hog = None

    @property
    def detector_name(self) -> str:
        return "OpenCV-HOG-Person-Detector-v1.0"

    @property
    def detection_source(self) -> str:
        return "COMPUTER_VISION"

    @property
    def is_simulation(self) -> bool:
        return False

    def detect_persons(
        self,
        frame_payload: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        frame = frame_payload.get("frame_data")
        now = frame_payload.get("timestamp") or datetime.now(timezone.utc)
        results = []

        if frame is None or not OPENCV_AVAILABLE or self._hog is None:
            return results

        try:
            # Resize for faster, stable inference if image is large
            h, w = frame.shape[:2]
            scale = 1.0
            if w > 800:
                scale = 800.0 / w
                frame_small = cv2.resize(frame, (800, int(h * scale)))
            else:
                frame_small = frame

            # HOG person detection
            rects, weights = self._hog.detectMultiScale(
                frame_small,
                winStride=(4, 4),
                padding=(8, 8),
                scale=1.05
            )

            for i, ((x, y, bw, bh), weight) in enumerate(zip(rects, weights)):
                # Map back to original coordinate scale
                orig_x = float(x / scale)
                orig_y = float(y / scale)
                orig_w = float(bw / scale)
                orig_h = float(bh / scale)
                conf = float(min(1.0, max(0.4, float(weight))))

                results.append({
                    "person_id": f"CV_PERSON_{i + 1:02d}",
                    "worker_id": None,
                    "worker_name": None,
                    "bounding_box": BoundingBox(
                        x=orig_x,
                        y=orig_y,
                        width=orig_w,
                        height=orig_h
                    ).to_dict(),
                    "confidence": round(conf, 4),
                    "timestamp": now,
                    "detection_source": self.detection_source,
                    "is_simulation": False,
                    "current_zone": "General Site Area",
                    "is_high_risk_zone": False,
                })

        except Exception as e:
            print(f"[WARN] CVPersonDetector detection failed: {e}")

        return results
