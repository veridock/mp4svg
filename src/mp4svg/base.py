"""
Base classes and common functionality for MP4 to SVG converters
"""

import os
import struct
import hashlib
import base64
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Tuple
import cv2
import numpy as np


class BaseConverter(ABC):
    """Abstract base class for all MP4 to SVG converters"""
    
    @abstractmethod
    def convert(self, mp4_path: str, output_path: str, **kwargs) -> str:
        """Convert MP4 to SVG using specific encoding method"""
        pass
    
    @abstractmethod
    def extract(self, svg_path: str, output_mp4: str) -> bool:
        """Extract MP4 from SVG file"""
        pass
    
    def _get_video_metadata(self, mp4_path: str) -> Dict[str, Any]:
        """Extract metadata from video file"""
        cap = cv2.VideoCapture(mp4_path)
        metadata = {
            'width': int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            'height': int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            'fps': cap.get(cv2.CAP_PROP_FPS),
            'frame_count': int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
            'duration': cap.get(cv2.CAP_PROP_FRAME_COUNT) / cap.get(cv2.CAP_PROP_FPS) if cap.get(cv2.CAP_PROP_FPS) > 0 else 0
        }
        cap.release()
        return metadata
    
    def _create_thumbnail(self, mp4_path: str, max_height: int = 120) -> Tuple[str, int, int]:
        """Create Base64 encoded thumbnail from first frame"""
        cap = cv2.VideoCapture(mp4_path)
        ret, frame = cap.read()
        thumbnail_b64 = ""
        thumb_width = thumb_height = 0
        
        if ret:
            height, width = frame.shape[:2]
            thumb_height = max_height
            thumb_width = int(width * thumb_height / height)
            thumbnail = cv2.resize(frame, (thumb_width, thumb_height))
            
            # Convert to JPEG and encode as base64
            _, buffer = cv2.imencode('.jpg', thumbnail)
            thumbnail_b64 = base64.b64encode(buffer).decode('ascii')
        
        cap.release()
        return thumbnail_b64, thumb_width, thumb_height
    
    def _validate_input(self, mp4_path: str) -> None:
        """Validate input MP4 file"""
        if not os.path.exists(mp4_path):
            raise FileNotFoundError(f"Input file not found: {mp4_path}")
        
        if not mp4_path.lower().endswith('.mp4'):
            raise ValueError("Input file must be an MP4 video")
        
        # Test if file can be opened
        cap = cv2.VideoCapture(mp4_path)
        if not cap.isOpened():
            raise ValueError(f"Unable to open video file: {mp4_path}")
        cap.release()


class EncodingError(Exception):
    """Exception raised when encoding fails"""
    pass


class DecodingError(Exception):
    """Exception raised when decoding fails"""
    pass


class ValidationError(Exception):
    """Exception raised when validation fails"""
    pass
