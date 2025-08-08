"""
MP4SVG - Video to SVG Converter Package
Convert MP4 videos to SVG containers using various encoding methods
"""

__version__ = "1.0.1"

# Import converters from the converters subpackage
from .converters import (
    ASCII85SVGConverter,
    PolyglotSVGConverter, 
    SVGVectorFrameConverter,
    QRCodeSVGConverter,
    HybridSVGConverter,
    
    # Legacy aliases for backward compatibility
    ASCII85Converter,
    PolyglotConverter,
    VectorConverter,
    QRCodeConverter,
    HybridConverter,
    
    # Utility functions
    get_converter,
    list_converters,
    CONVERTER_REGISTRY
)

# Import base classes and exceptions
from .base import BaseConverter, EncodingError, DecodingError, ValidationError

__all__ = [
    # Version info
    '__version__',
    
    # Main converters (new naming)
    'ASCII85SVGConverter',
    'PolyglotSVGConverter',
    'SVGVectorFrameConverter', 
    'QRCodeSVGConverter',
    'HybridSVGConverter',
    
    # Legacy converters (backward compatibility)
    'ASCII85Converter',
    'PolyglotConverter',
    'VectorConverter',
    'QRCodeConverter',
    'HybridConverter',
    
    # Base classes and exceptions
    'BaseConverter',
    'EncodingError',
    'DecodingError', 
    'ValidationError',
    
    # Utility functions
    'get_converter',
    'list_converters',
    'CONVERTER_REGISTRY'
]
