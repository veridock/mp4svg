"""
MP4SVG Converters Package

This package provides various methods for converting MP4 video files
to SVG containers with different encoding strategies.

Available Converters:
- ASCII85Converter: Base64-wrapped ASCII85 encoding (recommended)
- PolyglotConverter: Binary embedding in SVG comments  
- VectorConverter: Frame-to-vector path conversion
- QRCodeConverter: Chunked QR code embedding
- HybridConverter: Multi-method comparison tool
"""

from .ascii85_converter import ASCII85SVGConverter
from .polyglot_converter import PolyglotSVGConverter
from .vector_converter import SVGVectorFrameConverter
from .qrcode_converter import QRCodeSVGConverter
from .hybrid_converter import HybridSVGConverter

# Keep legacy imports for backward compatibility
from .ascii85_converter import ASCII85SVGConverter as ASCII85Converter
from .polyglot_converter import PolyglotSVGConverter as PolyglotConverter
from .vector_converter import SVGVectorFrameConverter as VectorConverter
from .qrcode_converter import QRCodeSVGConverter as QRCodeConverter
from .hybrid_converter import HybridSVGConverter as HybridConverter

__all__ = [
    # New naming convention
    'ASCII85SVGConverter',
    'PolyglotSVGConverter', 
    'SVGVectorFrameConverter',
    'QRCodeSVGConverter',
    'HybridSVGConverter',
    
    # Legacy naming for backward compatibility
    'ASCII85Converter',
    'PolyglotConverter',
    'VectorConverter',
    'QRCodeConverter',
    'HybridConverter',
]

# Converter registry for dynamic loading
CONVERTER_REGISTRY = {
    'ascii85': ASCII85SVGConverter,
    'polyglot': PolyglotSVGConverter,
    'vector': SVGVectorFrameConverter,
    'qrcode': QRCodeSVGConverter,
    'hybrid': HybridSVGConverter,
}

def get_converter(name: str):
    """Get converter class by name"""
    if name not in CONVERTER_REGISTRY:
        raise ValueError(f"Unknown converter: {name}. Available: {list(CONVERTER_REGISTRY.keys())}")
    return CONVERTER_REGISTRY[name]

def list_converters():
    """List all available converters"""
    return list(CONVERTER_REGISTRY.keys())
