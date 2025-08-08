"""
MP4 to SVG Converter Suite
Complete set of converters for different encoding methods
"""

from .ascii85 import ASCII85SVGConverter
from .polyglot import PolyglotSVGConverter  
from .vector import SVGVectorFrameConverter
from .qrcode import QRCodeSVGConverter
from .hybrid import HybridSVGConverter
from .base import BaseConverter, EncodingError, DecodingError, ValidationError

__version__ = "1.0.0"
__author__ = "Tom"

__all__ = [
    "ASCII85SVGConverter",
    "PolyglotSVGConverter", 
    "SVGVectorFrameConverter",
    "QRCodeSVGConverter",
    "HybridSVGConverter",
    "BaseConverter",
    "EncodingError",
    "DecodingError", 
    "ValidationError"
]
