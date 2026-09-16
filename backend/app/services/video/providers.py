"""
Video Stream Providers — Milestone 3 Phase 3.1
==============================================
Defines the clean abstraction and pluggable implementations for video stream ingestion:
- BaseVideoStreamProvider (abstract interface)
- DemoVideoProvider (deterministic simulated video source)
- LocalVideoProvider (local video file / webcam OpenCV reader)
- FutureRTSPProvider (network IP camera / RTSP / WebRTC stream adapter)
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Tuple
from datetime import datetime, timezone
import uuid
import time
import os

try:
    import cv2
    import numpy as np
    OPENCV_AVAILABLE = True
except ImportError:
    cv2 = None
    np = None
    OPENCV_AVAILABLE = False


class BaseVideoStreamProvider(ABC):
    """
    Abstract contract for video stream providers.
    Allows RTSP, WebRTC, local video, and simulation streams to be swapped
    without changing analysis pipeline or API logic.
    """

    def __init__(
        self,
        stream_id: str,
        site_id: str,
        camera_name: str = "Site Camera",
        fps: float = 15.0,
        resolution: Tuple[int, int] = (1280, 720),
        sampling_interval_frames: int = 5,
        confidence_threshold: float = 0.65,
    ):
        self.stream_id = stream_id
        self.site_id = site_id
        self.camera_name = camera_name
        self.fps = fps
        self.resolution_width, self.resolution_height = resolution
        self.sampling_interval_frames = sampling_interval_frames
        self.confidence_threshold = confidence_threshold

        self.is_active = False
        self.total_frames_ingested = 0
        self.processed_frames_count = 0
        self.dropped_frames_count = 0
        self.started_at: Optional[datetime] = None
        self.stopped_at: Optional[datetime] = None
        self.last_frame_timestamp: Optional[datetime] = None
        self.error_message: Optional[str] = None

    @property
    @abstractmethod
    def source_type(self) -> str:
        """Return provider type identifier: DEMO | LOCAL | RTSP"""
        pass

    @property
    @abstractmethod
    def is_simulation(self) -> bool:
        """True if the stream is synthetic/simulated; False if real CV source."""
        pass

    @property
    def label(self) -> str:
        """Explicit labeling requirement: DEMO / SIMULATION vs COMPUTER_VISION"""
        return "DEMO / SIMULATION" if self.is_simulation else "COMPUTER_VISION"

    @abstractmethod
    def start(self) -> bool:
        """Initialize and start the video source."""
        pass

    @abstractmethod
    def stop(self) -> bool:
        """Stop and release resources."""
        pass

    @abstractmethod
    def read_next_frame(self) -> Optional[Dict[str, Any]]:
        """
        Read next frame payload from source.
        Returns dictionary containing:
          - frame_number: int
          - timestamp: datetime
          - width: int
          - height: int
          - frame_data: raw bytes or ndarray (if available)
          - is_keyframe / should_process: bool (based on sampling interval)
          - simulated_metadata: Optional dict (for demo scenarios)
        """
        pass

    def get_status(self) -> Dict[str, Any]:
        """Return current operational status of the stream."""
        return {
            "stream_id": self.stream_id,
            "site_id": self.site_id,
            "camera_name": self.camera_name,
            "source_type": self.source_type,
            "is_active": self.is_active,
            "is_simulation": self.is_simulation,
            "label": self.label,
            "fps": self.fps,
            "resolution": f"{self.resolution_width}x{self.resolution_height}",
            "total_frames_ingested": self.total_frames_ingested,
            "processed_frames_count": self.processed_frames_count,
            "dropped_frames_count": self.dropped_frames_count,
            "sampling_interval": self.sampling_interval_frames,
            "confidence_threshold": self.confidence_threshold,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "stopped_at": self.stopped_at.isoformat() if self.stopped_at else None,
            "error": self.error_message,
        }


class DemoVideoProvider(BaseVideoStreamProvider):
    """
    Deterministic simulated video stream provider.
    Generates synthetic frames and metadata for repeatable demo scenarios
    without requiring physical camera hardware.
    """

    def __init__(
        self,
        stream_id: str,
        site_id: str,
        camera_name: str = "Demo Site Camera",
        fps: float = 15.0,
        resolution: Tuple[int, int] = (1280, 720),
        sampling_interval_frames: int = 5,
        confidence_threshold: float = 0.65,
        active_scenario_id: int = 1,
    ):
        super().__init__(
            stream_id=stream_id,
            site_id=site_id,
            camera_name=camera_name,
            fps=fps,
            resolution=resolution,
            sampling_interval_frames=sampling_interval_frames,
            confidence_threshold=confidence_threshold,
        )
        self.active_scenario_id = active_scenario_id
        self._current_frame_index = 0

    @property
    def source_type(self) -> str:
        return "DEMO"

    @property
    def is_simulation(self) -> bool:
        return True

    def set_scenario(self, scenario_id: int):
        self.active_scenario_id = scenario_id

    def start(self) -> bool:
        self.is_active = True
        self.started_at = datetime.now(timezone.utc)
        self.stopped_at = None
        self.error_message = None
        return True

    def stop(self) -> bool:
        self.is_active = False
        self.stopped_at = datetime.now(timezone.utc)
        return True

    def read_next_frame(self) -> Optional[Dict[str, Any]]:
        if not self.is_active:
            return None

        self._current_frame_index += 1
        self.total_frames_ingested += 1

        # Determine if this frame should be sampled for CV processing
        should_process = (self._current_frame_index % self.sampling_interval_frames) == 0

        if should_process:
            self.processed_frames_count += 1
        else:
            self.dropped_frames_count += 1

        now = datetime.now(timezone.utc)
        self.last_frame_timestamp = now

        return {
            "frame_number": self._current_frame_index,
            "timestamp": now,
            "width": self.resolution_width,
            "height": self.resolution_height,
            "should_process": should_process,
            "is_simulation": True,
            "scenario_id": self.active_scenario_id,
            "detection_source": "DEMO / SIMULATION",
            "frame_data": None,
        }


class LocalVideoProvider(BaseVideoStreamProvider):
    """
    Local video file / webcam stream provider using OpenCV cv2.VideoCapture.
    """

    def __init__(
        self,
        stream_id: str,
        site_id: str,
        video_path_or_device: Any = 0,
        camera_name: str = "Local Video Device",
        fps: float = 24.0,
        resolution: Tuple[int, int] = (1280, 720),
        sampling_interval_frames: int = 5,
        confidence_threshold: float = 0.65,
    ):
        super().__init__(
            stream_id=stream_id,
            site_id=site_id,
            camera_name=camera_name,
            fps=fps,
            resolution=resolution,
            sampling_interval_frames=sampling_interval_frames,
            confidence_threshold=confidence_threshold,
        )
        self.video_path_or_device = video_path_or_device
        self._cap = None
        self._current_frame_index = 0

    @property
    def source_type(self) -> str:
        return "LOCAL"

    @property
    def is_simulation(self) -> bool:
        return False

    def start(self) -> bool:
        if not OPENCV_AVAILABLE:
            self.error_message = "OpenCV (cv2) is not installed in the environment."
            return False

        try:
            self._cap = cv2.VideoCapture(self.video_path_or_device)
            if not self._cap.isOpened():
                self.error_message = f"Failed to open video source: {self.video_path_or_device}"
                return False

            w = int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or self.resolution_width
            h = int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or self.resolution_height
            fps = float(self._cap.get(cv2.CAP_PROP_FPS)) or self.fps

            self.resolution_width = w
            self.resolution_height = h
            self.fps = fps if fps > 0 else 15.0
            self.is_active = True
            self.started_at = datetime.now(timezone.utc)
            self.stopped_at = None
            return True
        except Exception as e:
            self.error_message = f"Local video initialization error: {str(e)}"
            return False

    def stop(self) -> bool:
        self.is_active = False
        self.stopped_at = datetime.now(timezone.utc)
        if self._cap is not None:
            try:
                self._cap.release()
            except Exception:
                pass
            self._cap = None
        return True

    def read_next_frame(self) -> Optional[Dict[str, Any]]:
        if not self.is_active:
            return None

        if self._cap is None:
            return None

        ret, frame = self._cap.read()
        if not ret:
            return None

        self._current_frame_index += 1
        self.total_frames_ingested += 1

        should_process = (self._current_frame_index % self.sampling_interval_frames) == 0
        if should_process:
            self.processed_frames_count += 1
        else:
            self.dropped_frames_count += 1

        now = datetime.now(timezone.utc)
        self.last_frame_timestamp = now

        return {
            "frame_number": self._current_frame_index,
            "timestamp": now,
            "width": self.resolution_width,
            "height": self.resolution_height,
            "should_process": should_process,
            "is_simulation": False,
            "detection_source": "COMPUTER_VISION",
            "frame_data": frame,
        }


class FutureRTSPProvider(BaseVideoStreamProvider):
    """
    RTSP / WebRTC / IP Camera video provider skeleton.
    Allows RTSP streams (e.g. rtsp://camera-ip:554/live) to be integrated
    seamlessly with connection timeouts, reconnect handling, and validation.
    """

    def __init__(
        self,
        stream_id: str,
        site_id: str,
        rtsp_url: str,
        camera_name: str = "IP Camera RTSP",
        fps: float = 20.0,
        resolution: Tuple[int, int] = (1920, 1080),
        sampling_interval_frames: int = 5,
        confidence_threshold: float = 0.65,
        timeout_seconds: int = 5,
    ):
        super().__init__(
            stream_id=stream_id,
            site_id=site_id,
            camera_name=camera_name,
            fps=fps,
            resolution=resolution,
            sampling_interval_frames=sampling_interval_frames,
            confidence_threshold=confidence_threshold,
        )
        self.rtsp_url = rtsp_url
        self.timeout_seconds = timeout_seconds
        self._cap = None
        self._current_frame_index = 0

    @property
    def source_type(self) -> str:
        return "RTSP"

    @property
    def is_simulation(self) -> bool:
        return False

    def start(self) -> bool:
        if not self.rtsp_url or not self.rtsp_url.startswith(("rtsp://", "http://", "https://")):
            self.error_message = f"Invalid RTSP URL: {self.rtsp_url}"
            return False

        if not OPENCV_AVAILABLE:
            self.error_message = "OpenCV (cv2) is required for RTSP video capture."
            return False

        try:
            os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;udp"
            self._cap = cv2.VideoCapture(self.rtsp_url)
            if not self._cap.isOpened():
                self.error_message = f"Could not connect to RTSP endpoint: {self.rtsp_url}"
                return False

            self.is_active = True
            self.started_at = datetime.now(timezone.utc)
            self.stopped_at = None
            return True
        except Exception as e:
            self.error_message = f"RTSP connection failed: {str(e)}"
            return False

    def stop(self) -> bool:
        self.is_active = False
        self.stopped_at = datetime.now(timezone.utc)
        if self._cap is not None:
            try:
                self._cap.release()
            except Exception:
                pass
            self._cap = None
        return True

    def read_next_frame(self) -> Optional[Dict[str, Any]]:
        if not self.is_active or self._cap is None:
            return None

        ret, frame = self._cap.read()
        if not ret:
            self.dropped_frames_count += 1
            return None

        self._current_frame_index += 1
        self.total_frames_ingested += 1

        should_process = (self._current_frame_index % self.sampling_interval_frames) == 0
        if should_process:
            self.processed_frames_count += 1
        else:
            self.dropped_frames_count += 1

        now = datetime.now(timezone.utc)
        self.last_frame_timestamp = now

        return {
            "frame_number": self._current_frame_index,
            "timestamp": now,
            "width": self.resolution_width,
            "height": self.resolution_height,
            "should_process": should_process,
            "is_simulation": False,
            "detection_source": "COMPUTER_VISION",
            "frame_data": frame,
        }
