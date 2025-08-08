"""
Tests for mp4svg validators
"""

import os
import tempfile
import pytest
from unittest.mock import Mock, patch

from src.mp4svg.validators import SVGValidator, IntegrityValidator
from src.mp4svg.base import ValidationError


class TestSVGValidator:
    """Test SVG validation functionality"""

    def setup_method(self):
        self.validator = SVGValidator()
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_validate_well_formed_svg(self):
        """Test validation of well-formed SVG"""
        svg_content = '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">
    <rect width="50" height="50" fill="red"/>
</svg>'''
        
        svg_file = os.path.join(self.temp_dir, 'test.svg')
        with open(svg_file, 'w') as f:
            f.write(svg_content)
        
        result = self.validator.validate_svg_file(svg_file)
        
        assert result['is_well_formed'] is True
        assert result['is_valid'] is True
        assert len(result['errors']) == 0

    def test_validate_malformed_xml(self):
        """Test validation of malformed XML"""
        svg_content = '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">
    <rect width="50" height="50" fill="red"
</svg>'''  # Missing closing bracket
        
        svg_file = os.path.join(self.temp_dir, 'test.svg')
        with open(svg_file, 'w') as f:
            f.write(svg_content)
        
        result = self.validator.validate_svg_file(svg_file)
        
        assert result['is_well_formed'] is False
        assert result['is_valid'] is False
        assert len(result['errors']) > 0

    def test_detect_ascii85_format(self):
        """Test detection of ASCII85 format"""
        svg_content = '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg"
     xmlns:video="http://example.org/video/2024"
     width="640" height="480">
    <metadata>
        <video:data encoding="ascii85" originalSize="1000" fps="30" frames="300">
            <![CDATA[test_data]]>
        </video:data>
    </metadata>
</svg>'''
        
        svg_file = os.path.join(self.temp_dir, 'test.svg')
        with open(svg_file, 'w') as f:
            f.write(svg_content)
        
        result = self.validator.validate_svg_file(svg_file)
        
        assert result['detected_format'] == 'ascii85'
        assert result['metadata']['encoding'] == 'ascii85'
        assert result['metadata']['originalSize'] == '1000'

    def test_detect_polyglot_format(self):
        """Test detection of polyglot format"""
        svg_content = '''<!--POLYGLOT_BOUNDARY_abc123
<!--MP4_DATA
dGVzdCBkYXRh
MP4_DATA-->
POLYGLOT_BOUNDARY_abc123-->
<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">
    <rect width="50" height="50" fill="blue"/>
</svg>'''
        
        svg_file = os.path.join(self.temp_dir, 'test.svg')
        with open(svg_file, 'w') as f:
            f.write(svg_content)
        
        result = self.validator.validate_svg_file(svg_file)
        
        assert result['detected_format'] == 'polyglot'

    def test_detect_qrcode_format(self):
        """Test detection of QR code format"""
        svg_content = '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="400" height="400">
    <g id="qr-frame-0">
        <image href="data:image/png;base64,test"/>
    </g>
    <g id="qr-frame-1">
        <image href="data:image/png;base64,test"/>
    </g>
</svg>'''
        
        svg_file = os.path.join(self.temp_dir, 'test.svg')
        with open(svg_file, 'w') as f:
            f.write(svg_content)
        
        result = self.validator.validate_svg_file(svg_file)
        
        assert result['detected_format'] == 'qrcode'

    def test_detect_vector_format(self):
        """Test detection of vector format"""
        svg_content = '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">
    <g id="frame-0">
        <path d="M 10,10 L 50,10 L 30,40 Z"/>
        <set attributeName="opacity" to="1" begin="0s"/>
    </g>
</svg>'''
        
        svg_file = os.path.join(self.temp_dir, 'test.svg')
        with open(svg_file, 'w') as f:
            f.write(svg_content)
        
        result = self.validator.validate_svg_file(svg_file)
        
        assert result['detected_format'] == 'vector'

    def test_validate_missing_file(self):
        """Test validation of missing file"""
        with pytest.raises(FileNotFoundError):
            self.validator.validate_svg_file('nonexistent.svg')

    def test_validate_ascii85_format_specific(self):
        """Test ASCII85 format-specific validation"""
        # Test with missing video data
        svg_content = '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">
    <rect width="50" height="50" fill="red"/>
</svg>'''
        
        svg_file = os.path.join(self.temp_dir, 'test.svg')
        with open(svg_file, 'w') as f:
            f.write(svg_content)
        
        # Force format detection to ASCII85
        with patch.object(self.validator, '_detect_format', return_value='ascii85'):
            result = self.validator.validate_svg_file(svg_file)
            
            assert any('video:data element not found' in error for error in result['errors'])

    def test_large_file_warning(self):
        """Test warning for large files"""
        # Create a large SVG content
        large_content = '<?xml version="1.0" encoding="UTF-8"?>\n<svg xmlns="http://www.w3.org/2000/svg">'
        large_content += 'A' * (50 * 1024 * 1024)  # 50MB of data
        large_content += '</svg>'
        
        svg_file = os.path.join(self.temp_dir, 'large.svg')
        with open(svg_file, 'w') as f:
            f.write(large_content)
        
        result = self.validator.validate_svg_file(svg_file)
        
        assert any('Large file size' in warning for warning in result['warnings'])


class TestIntegrityValidator:
    """Test integrity validation functionality"""

    def setup_method(self):
        self.validator = IntegrityValidator()
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_detect_ascii85_format(self):
        """Test ASCII85 format detection"""
        svg_content = '''<?xml version="1.0"?>
<svg xmlns:video="http://example.org/video/2024">
    <video:data encoding="ascii85">test</video:data>
</svg>'''
        
        svg_file = os.path.join(self.temp_dir, 'test.svg')
        with open(svg_file, 'w') as f:
            f.write(svg_content)
        
        format_type = self.validator._detect_format(svg_file)
        assert format_type == 'ascii85'

    def test_detect_polyglot_format(self):
        """Test polyglot format detection"""
        svg_content = '''<!--POLYGLOT_BOUNDARY_test123-->
<svg>test</svg>'''
        
        svg_file = os.path.join(self.temp_dir, 'test.svg')
        with open(svg_file, 'w') as f:
            f.write(svg_content)
        
        format_type = self.validator._detect_format(svg_file)
        assert format_type == 'polyglot'

    def test_detect_qrcode_format(self):
        """Test QR code format detection"""
        svg_content = '''<svg>
    <g id="qr-frame-0">test</g>
</svg>'''
        
        svg_file = os.path.join(self.temp_dir, 'test.svg')
        with open(svg_file, 'w') as f:
            f.write(svg_content)
        
        format_type = self.validator._detect_format(svg_file)
        assert format_type == 'qrcode'

    def test_detect_vector_format(self):
        """Test vector format detection"""
        svg_content = '''<svg>
    <path d="M 10,10 L 50,50"/>
    <set attributeName="opacity"/>
</svg>'''
        
        svg_file = os.path.join(self.temp_dir, 'test.svg')
        with open(svg_file, 'w') as f:
            f.write(svg_content)
        
        format_type = self.validator._detect_format(svg_file)
        assert format_type == 'vector'

    def test_detect_unknown_format(self):
        """Test unknown format detection"""
        svg_content = '''<svg><rect/></svg>'''
        
        svg_file = os.path.join(self.temp_dir, 'test.svg')
        with open(svg_file, 'w') as f:
            f.write(svg_content)
        
        format_type = self.validator._detect_format(svg_file)
        assert format_type is None

    @patch('src.mp4svg.ascii85.ASCII85SVGConverter.extract')
    def test_validate_integrity_ascii85_success(self, mock_extract):
        """Test successful ASCII85 integrity validation"""
        # Mock successful extraction
        def mock_extract_func(svg_path, output_path):
            with open(output_path, 'wb') as f:
                f.write(b'test data')
            return True
        
        mock_extract.side_effect = mock_extract_func
        
        # Create test SVG
        svg_content = '''<svg xmlns:video="http://example.org/video/2024">
    <video:data encoding="ascii85">test</video:data>
</svg>'''
        
        svg_file = os.path.join(self.temp_dir, 'test.svg')
        with open(svg_file, 'w') as f:
            f.write(svg_content)
        
        # Create original MP4 for comparison
        original_mp4 = os.path.join(self.temp_dir, 'original.mp4')
        with open(original_mp4, 'wb') as f:
            f.write(b'test data')
        
        result = self.validator.validate_integrity(svg_file, original_mp4)
        
        assert result['format_detected'] == 'ascii85'
        assert result['extraction_successful'] is True
        assert result['data_integrity_valid'] is True
        assert result['size_match'] is True
        assert result['checksum_match'] is True

    def test_validate_integrity_no_original(self):
        """Test integrity validation without original file"""
        svg_content = '''<svg xmlns:video="http://example.org/video/2024">
    <video:data encoding="ascii85">test</video:data>
</svg>'''
        
        svg_file = os.path.join(self.temp_dir, 'test.svg')
        with open(svg_file, 'w') as f:
            f.write(svg_content)
        
        with patch.object(self.validator, '_extract_data', return_value=b'test data'):
            result = self.validator.validate_integrity(svg_file)
            
            assert result['extraction_successful'] is True
            assert 'No original MP4 provided' in result['warnings'][0]

    def test_validate_integrity_extraction_failed(self):
        """Test integrity validation with failed extraction"""
        svg_content = '''<svg><rect/></svg>'''
        
        svg_file = os.path.join(self.temp_dir, 'test.svg')
        with open(svg_file, 'w') as f:
            f.write(svg_content)
        
        result = self.validator.validate_integrity(svg_file)
        
        assert result['format_detected'] is None
        assert result['extraction_successful'] is False
        assert 'Could not detect mp4svg format' in result['errors']

    def test_batch_validate_empty_directory(self):
        """Test batch validation with empty directory"""
        empty_dir = os.path.join(self.temp_dir, 'empty')
        os.makedirs(empty_dir)
        
        result = self.validator.batch_validate(empty_dir)
        
        assert result['total_files'] == 0
        assert result['files_processed'] == 0
        assert result['files_valid'] == 0

    def test_batch_validate_with_files(self):
        """Test batch validation with SVG files"""
        # Create test SVG files
        for i in range(3):
            svg_content = f'''<svg xmlns:video="http://example.org/video/2024">
    <video:data encoding="ascii85">test data {i}</video:data>
</svg>'''
            svg_file = os.path.join(self.temp_dir, f'test{i}.svg')
            with open(svg_file, 'w') as f:
                f.write(svg_content)
        
        with patch.object(self.validator, 'validate_integrity') as mock_validate:
            mock_validate.return_value = {
                'format_detected': 'ascii85',
                'extraction_successful': True,
                'data_integrity_valid': True,
                'errors': []
            }
            
            result = self.validator.batch_validate(self.temp_dir)
            
            assert result['total_files'] == 3
            assert result['files_processed'] == 3
            assert result['files_valid'] == 3
            assert result['files_with_errors'] == 0

    def test_validate_embedded_checksums_qr(self):
        """Test embedded checksum validation for QR format"""
        svg_content = '''<?xml version="1.0"?>
<svg>
    <metadata>{"checksum": "abc123", "chunks": 5, "total_size": 1000}</metadata>
    <g id="qr-frame-0"><image/></g>
</svg>'''
        
        svg_file = os.path.join(self.temp_dir, 'test.svg')
        with open(svg_file, 'w') as f:
            f.write(svg_content)
        
        result = self.validator.validate_embedded_checksums(svg_file)
        
        assert result['has_embedded_checksums'] is True
        assert result['checksum_details']['overall_checksum'] == 'abc123'
        assert result['checksum_details']['chunks'] == 5

    def test_validate_embedded_checksums_polyglot(self):
        """Test embedded checksum validation for polyglot format"""
        svg_content = '''<!--POLYGLOT_BOUNDARY_test-->
Summary: SVG Polyglot Container
- Original MP4: 1,000 bytes
- Total embedded: 1,500 bytes
<!--POLYGLOT_BOUNDARY_test-->'''
        
        svg_file = os.path.join(self.temp_dir, 'test.svg')
        with open(svg_file, 'w') as f:
            f.write(svg_content)
        
        result = self.validator.validate_embedded_checksums(svg_file)
        
        assert result['has_embedded_checksums'] is True
        assert result['checksums_valid'] is True
        assert 1000 in result['checksum_details']['embedded_sizes']
        assert 1500 in result['checksum_details']['embedded_sizes']


class TestValidationIntegration:
    """Integration tests for validation components"""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_full_validation_pipeline(self):
        """Test complete validation pipeline"""
        # Create a realistic ASCII85 SVG
        svg_content = '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg"
     xmlns:video="http://example.org/video/2024"
     width="640" height="480">

    <title>ASCII85 Encoded Video</title>
    <desc>Video data encoded with ASCII85 (25% overhead)</desc>

    <metadata>
        <video:data encoding="ascii85" 
                    originalSize="1000"
                    fps="30"
                    frames="300"
                    id="videoData">
            <![CDATA[
PGZha2UgZGF0YSBmb3IgdGVzdGluZz4=
            ]]>
        </video:data>
    </metadata>

    <rect width="100%" height="100%" fill="#1a1a1a"/>
    <text x="50%" y="50%" text-anchor="middle" fill="#0f0">
        ASCII85 Video Container
    </text>
</svg>'''
        
        svg_file = os.path.join(self.temp_dir, 'test.svg')
        with open(svg_file, 'w') as f:
            f.write(svg_content)
        
        # Run SVG validation
        svg_validator = SVGValidator()
        svg_result = svg_validator.validate_svg_file(svg_file)
        
        # Run integrity validation
        integrity_validator = IntegrityValidator()
        integrity_result = integrity_validator.validate_integrity(svg_file)
        
        # Verify results
        assert svg_result['is_well_formed'] is True
        assert svg_result['detected_format'] == 'ascii85'
        assert svg_result['metadata']['encoding'] == 'ascii85'
        
        assert integrity_result['format_detected'] == 'ascii85'
        # Note: Without actual extraction, some checks will fail
        # but format detection should work
