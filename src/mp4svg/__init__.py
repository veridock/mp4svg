"""
MP4 to SVG Converter Suite
Complete set of converters for different encoding methods
"""

from .converters import (
    PolyglotSVGConverter,
    ASCII85SVGConverter, 
    SVGVectorFrameConverter,
    QRCodeSVGConverter,
    HybridSVGConverter
)

__version__ = "1.0.0"
__author__ = "Tom"

__all__ = [
    "PolyglotSVGConverter",
    "ASCII85SVGConverter", 
    "SVGVectorFrameConverter",
    "QRCodeSVGConverter",
    "HybridSVGConverter"
]
