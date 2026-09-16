"""
Mock / Test Computer Vision PPE Detector
=========================================
EXPLICITLY LABELED AS: DEMO / MOCK
Used ONLY for deterministic unit tests and controlled test scenarios.
Never claimed as real Computer Vision execution.
"""

from typing import List, Dict, Any, Optional
import uuid

from app.services.cv.base_detector import (
    BasePPEDetector, DetectorOutput, PersonDetection, RawPPEDetection, BoundingBox
)


from app.models.models import PPEComplianceStatus


# Re-export reference for demo scenario definitions
PPE_DEMO_SCENARIOS: Dict[int, Dict[str, Any]] = {
    1: {
        "id": 1,
        "name": "Scenario 1 — Fully Compliant Worker",
        "description": "Worker wearing certified Hard Hat, High-Visibility Vest, and Safety Goggles. Full compliance verified by Computer Vision.",
        "expected_compliance": PPEComplianceStatus.COMPLIANT,
        "expected_findings_count": 0,
        "detected_items": ["HARD_HAT", "SAFETY_VEST", "SAFETY_GOGGLES"],
        "missing_items": [],
    },
    2: {
        "id": 2,
        "name": "Scenario 2 — Missing Hard Hat",
        "description": "Worker wearing Safety Vest and Goggles, but Hard Hat is absent in active construction zone.",
        "expected_compliance": PPEComplianceStatus.NON_COMPLIANT,
        "expected_findings_count": 1,
        "detected_items": ["SAFETY_VEST", "SAFETY_GOGGLES"],
        "missing_items": ["HARD_HAT"],
    },
    3: {
        "id": 3,
        "name": "Scenario 3 — Multiple PPE Violations",
        "description": "Worker with multiple critical PPE deficiencies (Missing Hard Hat and Missing Goggles) during active construction activity.",
        "expected_compliance": PPEComplianceStatus.NON_COMPLIANT,
        "expected_findings_count": 2,
        "detected_items": ["SAFETY_VEST"],
        "missing_items": ["HARD_HAT", "SAFETY_GOGGLES"],
    },
    4: {
        "id": 4,
        "name": "Scenario 4 — Low Confidence Detection",
        "description": "Obscured camera angle or low lighting causing optical detection confidence to fall below threshold (0.65). Marked as UNCERTAIN.",
        "expected_compliance": PPEComplianceStatus.UNCERTAIN,
        "expected_findings_count": 1,
        "detected_items": ["HARD_HAT (LOW_CONFIDENCE)", "SAFETY_VEST (LOW_CONFIDENCE)"],
        "missing_items": [],
    },
    5: {
        "id": 5,
        "name": "Scenario 5 — Database vs CV Discrepancy",
        "description": "Worker recorded as COMPLIANT in safety registry, but Computer Vision analysis reveals missing Hard Hat on active site.",
        "expected_compliance": PPEComplianceStatus.NON_COMPLIANT,
        "expected_findings_count": 2,
        "detected_items": ["SAFETY_VEST"],
        "missing_items": ["HARD_HAT"],
    },
}


class MockPPEDetector(BasePPEDetector):
    """
    Test fixture adapter for deterministic unit testing.
    Explicitly labeled as 'DEMO / MOCK'.
    """

    def __init__(self, forced_scenario: Optional[int] = None):
        self._model_name = "MOCK-TEST-ADAPTER-v1.0"
        self._detection_source = "DEMO / MOCK"
        self.forced_scenario = forced_scenario

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def detection_source(self) -> str:
        return self._detection_source

    def detect(self, image_path: str, context: Optional[Dict[str, Any]] = None) -> DetectorOutput:
        scenario = self.forced_scenario or (context.get("scenario_id") if context else None) or 1
        w_img, h_img = 800, 600

        px, py, pw, ph = 200, 60, 400, 500
        person_box = BoundingBox(x=float(px), y=float(py), width=float(pw), height=float(ph))
        person_id = "P-01"

        detections: List[RawPPEDetection] = []
        missing_ppe: List[str] = []

        if scenario == 1:
            # DEMO 1: FULL PPE (Hard Hat, Vest, Goggles) -> COMPLIANT
            detections = [
                RawPPEDetection(
                    detection_id="MOCK-DET-HH-01",
                    ppe_class="HARD_HAT",
                    confidence=0.94,
                    bounding_box=BoundingBox(x=250.0, y=50.0, width=300.0, height=120.0),
                    status="DETECTED",
                    is_compliant=True,
                    person_id=person_id,
                    detection_source=self.detection_source,
                ),
                RawPPEDetection(
                    detection_id="MOCK-DET-SV-01",
                    ppe_class="SAFETY_VEST",
                    confidence=0.92,
                    bounding_box=BoundingBox(x=220.0, y=180.0, width=360.0, height=240.0),
                    status="DETECTED",
                    is_compliant=True,
                    person_id=person_id,
                    detection_source=self.detection_source,
                ),
                RawPPEDetection(
                    detection_id="MOCK-DET-SG-01",
                    ppe_class="SAFETY_GOGGLES",
                    confidence=0.89,
                    bounding_box=BoundingBox(x=300.0, y=120.0, width=200.0, height=60.0),
                    status="DETECTED",
                    is_compliant=True,
                    person_id=person_id,
                    detection_source=self.detection_source,
                ),
            ]
            missing_ppe = []
            is_compliant = True

        elif scenario == 2:
            # DEMO 2: MISSING HARD HAT
            detections = [
                RawPPEDetection(
                    detection_id="MOCK-DET-SV-02",
                    ppe_class="SAFETY_VEST",
                    confidence=0.93,
                    bounding_box=BoundingBox(x=220.0, y=180.0, width=360.0, height=240.0),
                    status="DETECTED",
                    is_compliant=True,
                    person_id=person_id,
                    detection_source=self.detection_source,
                ),
                RawPPEDetection(
                    detection_id="MOCK-DET-SG-02",
                    ppe_class="SAFETY_GOGGLES",
                    confidence=0.87,
                    bounding_box=BoundingBox(x=300.0, y=120.0, width=200.0, height=60.0),
                    status="DETECTED",
                    is_compliant=True,
                    person_id=person_id,
                    detection_source=self.detection_source,
                ),
            ]
            missing_ppe = ["HARD_HAT"]
            is_compliant = False

        elif scenario == 3:
            # DEMO 3: MULTIPLE PPE VIOLATIONS (Missing Hard Hat & Missing Goggles)
            detections = [
                RawPPEDetection(
                    detection_id="MOCK-DET-SV-03",
                    ppe_class="SAFETY_VEST",
                    confidence=0.91,
                    bounding_box=BoundingBox(x=220.0, y=180.0, width=360.0, height=240.0),
                    status="DETECTED",
                    is_compliant=True,
                    person_id=person_id,
                    detection_source=self.detection_source,
                ),
            ]
            missing_ppe = ["HARD_HAT", "SAFETY_GOGGLES"]
            is_compliant = False

        elif scenario == 4:
            # DEMO 4: LOW CONFIDENCE (Uncertain detection below threshold)
            detections = [
                RawPPEDetection(
                    detection_id="MOCK-DET-HH-04",
                    ppe_class="HARD_HAT",
                    confidence=0.48,  # Below 0.65 threshold
                    bounding_box=BoundingBox(x=250.0, y=50.0, width=300.0, height=120.0),
                    status="LOW_CONFIDENCE",
                    is_compliant=False,
                    person_id=person_id,
                    detection_source=self.detection_source,
                ),
                RawPPEDetection(
                    detection_id="MOCK-DET-SV-04",
                    ppe_class="SAFETY_VEST",
                    confidence=0.52,  # Below threshold
                    bounding_box=BoundingBox(x=220.0, y=180.0, width=360.0, height=240.0),
                    status="LOW_CONFIDENCE",
                    is_compliant=False,
                    person_id=person_id,
                    detection_source=self.detection_source,
                ),
            ]
            missing_ppe = []
            is_compliant = False

        elif scenario == 5:
            # DEMO 5: DISCREPANCY (Worker recorded as compliant in DB, but Hard Hat missing in CV)
            detections = [
                RawPPEDetection(
                    detection_id="MOCK-DET-SV-05",
                    ppe_class="SAFETY_VEST",
                    confidence=0.95,
                    bounding_box=BoundingBox(x=220.0, y=180.0, width=360.0, height=240.0),
                    status="DETECTED",
                    is_compliant=True,
                    person_id=person_id,
                    detection_source=self.detection_source,
                ),
            ]
            missing_ppe = ["HARD_HAT"]
            is_compliant = False

        person = PersonDetection(
            person_id=person_id,
            bounding_box=person_box,
            confidence=0.95,
            detected_ppe=detections,
            missing_ppe=missing_ppe,
            is_compliant=is_compliant,
            worker_id=context.get("worker_id") if context else None,
            worker_name=context.get("worker_name") if context else None,
        )

        return DetectorOutput(
            image_width=w_img,
            image_height=h_img,
            persons=[person],
            detections=detections,
            model_name=self.model_name,
            detection_source=self.detection_source,
        )
