# MP4SVG - Video to SVG Converter

A Python package that converts MP4 video files into SVG containers using various encoding methods, with full roundtrip extraction capabilities.

## Features

- **Multiple Encoding Methods**: ASCII85, Polyglot, Vector Animation, QR Code, and Hybrid
- **XML-Safe Embedding**: Proper handling of binary data in SVG/XML context
- **Interactive SVG**: Embedded JavaScript for in-browser video playback
- **Thumbnail Previews**: JPEG thumbnails for system/browser compatibility
- **Data Integrity**: Built-in validation and checksum verification
- **CLI Interface**: Command-line tools for conversion and extraction
- **Extensible Architecture**: Modular design for easy extension

## Installation

### From Source
```bash
git clone <repository-url>
cd mp4svg
pip install -e .
```

### Dependencies
- Python 3.8+
- OpenCV (cv2)
- NumPy
- Pillow (PIL)
- qrcode
- lxml

## Quick Start

### Command Line Usage

```bash
# Convert MP4 to SVG using ASCII85 encoding
mp4svg input.mp4 output.svg --method ascii85

# Extract MP4 from SVG
mp4svg output.svg extracted.mp4 --extract

# Use polyglot method with custom chunk size
mp4svg input.mp4 output.svg --method polyglot --chunk-size 4096

# Convert to QR codes with error correction
mp4svg input.mp4 output.svg --method qrcode --error-correction M

# Try all methods and compare (hybrid)
mp4svg input.mp4 output.svg --method hybrid
```

### Python API

```python
from mp4svg import ASCII85SVGConverter, PolyglotSVGConverter

# ASCII85 encoding (recommended for most use cases)
converter = ASCII85SVGConverter()
svg_path = converter.convert('video.mp4', 'output.svg')

# Extract back to MP4
success = converter.extract('output.svg', 'extracted.mp4')

# Polyglot embedding (larger files, better compatibility)
polyglot = PolyglotSVGConverter()
svg_path = polyglot.convert('video.mp4', 'polyglot.svg')
```

## Encoding Methods

### 1. ASCII85 (Recommended)
- **Best for**: General use, good compression ratio
- **Overhead**: ~25% size increase
- **Features**: Interactive playback, thumbnail preview, XML-safe
- **Roundtrip**: Full fidelity extraction

```python
from mp4svg import ASCII85SVGConverter
converter = ASCII85SVGConverter()
```

### 2. Polyglot
- **Best for**: Maximum compatibility, embedded metadata
- **Overhead**: ~33% size increase  
- **Features**: SVG + embedded binary data, summary statistics
- **Roundtrip**: Full fidelity extraction

```python
from mp4svg import PolyglotSVGConverter
converter = PolyglotSVGConverter()
```

### 3. Vector Animation
- **Best for**: Stylized animation, artistic effects
- **Overhead**: Variable (depends on complexity)
- **Features**: True vector animation, scalable
- **Roundtrip**: Not supported (lossy conversion)

```python
from mp4svg import SVGVectorFrameConverter
converter = SVGVectorFrameConverter()
```

### 4. QR Code
- **Best for**: Educational purposes, distributed storage
- **Overhead**: Very high (~10x size increase)
- **Features**: Multiple QR frames, chunk-based storage
- **Roundtrip**: Full fidelity with extraction script

```python
from mp4svg import QRCodeSVGConverter
converter = QRCodeSVGConverter(chunk_size=1000)
```

### 5. Hybrid
- **Best for**: Comparing all methods, choosing optimal
- **Features**: Tests all methods, size comparison, format detection
- **Output**: Multiple files with performance report

```python
from mp4svg import HybridSVGConverter
converter = HybridSVGConverter()
```

## SVG Validation

The package includes comprehensive validation utilities:

```python
from mp4svg.validators import SVGValidator, IntegrityValidator

# Validate SVG structure and detect format
svg_validator = SVGValidator()
result = svg_validator.validate_svg_file('output.svg')

# Check data integrity and extraction
integrity_validator = IntegrityValidator()
integrity_result = integrity_validator.validate_integrity('output.svg', 'original.mp4')

# Batch validate directory
batch_result = integrity_validator.batch_validate('/path/to/svg/files/')
```

## Interactive SVG Features

Generated SVG files include:
- **Thumbnail Preview**: JPEG thumbnail for system compatibility
- **Play Button**: Click to decode and play video
- **JavaScript Decoder**: Built-in ASCII85/Base64 decoder
- **Error Handling**: Robust namespace and element selection

## Project Structure

```
mp4svg/
├── src/mp4svg/
│   ├── __init__.py          # Package exports
│   ├── base.py              # Base converter class
│   ├── ascii85.py           # ASCII85 converter
│   ├── polyglot.py          # Polyglot converter  
│   ├── vector.py            # Vector animation converter
│   ├── qrcode.py            # QR code converter
│   ├── hybrid.py            # Hybrid converter
│   ├── cli.py               # Command-line interface
│   └── validators/          # Validation utilities
│       ├── __init__.py
│       ├── svg_validator.py
│       └── integrity_validator.py
├── tests/                   # Test suite
├── pyproject.toml          # Poetry configuration
└── README.md               # This file
```

## Testing

Run the test suite:

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_converters.py -v

# Run with coverage
pytest --cov=src/mp4svg tests/
```

## Advanced Usage

### Custom Conversion Settings

```python
# ASCII85 with custom settings
converter = ASCII85SVGConverter()
converter.thumbnail_quality = 85
converter.max_size_mb = 50

# Polyglot with custom boundary
polyglot = PolyglotSVGConverter()
polyglot.chunk_size = 8192

# Vector with animation settings  
vector = SVGVectorFrameConverter()
vector.frame_duration = 0.1
vector.edge_threshold = 100

# QR with error correction
qr = QRCodeSVGConverter(
    chunk_size=500,
    error_correction='H',  # High error correction
    border=2
)
```

### Batch Processing

```python
import os
from mp4svg import ASCII85SVGConverter

converter = ASCII85SVGConverter()

# Convert all MP4 files in directory
input_dir = '/path/to/videos/'
output_dir = '/path/to/svg_output/'

for filename in os.listdir(input_dir):
    if filename.endswith('.mp4'):
        input_path = os.path.join(input_dir, filename)
        output_path = os.path.join(output_dir, filename.replace('.mp4', '.svg'))
        
        try:
            converter.convert(input_path, output_path)
            print(f"Converted: {filename}")
        except Exception as e:
            print(f"Failed to convert {filename}: {e}")
```

### Validation Pipeline

```python
from mp4svg.validators import SVGValidator, IntegrityValidator

# Complete validation pipeline
def validate_conversion(original_mp4, generated_svg):
    # Structure validation
    svg_validator = SVGValidator()
    svg_result = svg_validator.validate_svg_file(generated_svg)
    
    if not svg_result['is_well_formed']:
        print("SVG is not well-formed XML")
        return False
    
    # Integrity validation  
    integrity_validator = IntegrityValidator()
    integrity_result = integrity_validator.validate_integrity(
        generated_svg, original_mp4
    )
    
    if not integrity_result['data_integrity_valid']:
        print("Data integrity check failed")
        return False
        
    print(f"Validation successful: {svg_result['detected_format']} format")
    return True
```

## Troubleshooting

### Common Issues

1. **XML Parsing Errors**
   - Ensure input MP4 is not corrupted
   - Check file size limits (default: 100MB)
   - Validate with `SVGValidator`

2. **JavaScript Not Working in Browser**
   - Check browser console for errors
   - Ensure SVG is served with correct MIME type
   - Modern browser required for ES6 features

3. **Extraction Failures**
   - Verify SVG format detection
   - Check embedded data integrity
   - Use validation utilities

4. **Large File Performance**
   - Use chunked processing for very large videos
   - Consider polyglot method for better memory usage
   - Set appropriate `max_size_mb` limits

### Debug Mode

```python
import logging
logging.basicConfig(level=logging.DEBUG)

from mp4svg import ASCII85SVGConverter
converter = ASCII85SVGConverter()
# Detailed logging will be displayed
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Changelog

### v1.0.0
- Initial release with ASCII85, Polyglot, Vector, QR Code converters
- Interactive SVG with JavaScript playback
- Comprehensive validation utilities
- CLI interface
- Full test coverage