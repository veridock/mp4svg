"""
Unit tests for mp4svg converters
"""

import os
import tempfile
import pytest
from unittest.mock import Mock, patch, MagicMock
import numpy as np

from mp4svg import (
    ASCII85SVGConverter, PolyglotSVGConverter, 
    SVGVectorFrameConverter, QRCodeSVGConverter,
    HybridSVGConverter, EncodingError, DecodingError
)


class TestASCII85Converter:
    """Test ASCII85 converter functionality"""

    def setup_method(self):
        self.converter = ASCII85SVGConverter()
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_ascii85_encoding_basic(self):
        """Test basic ASCII85 encoding"""
        test_data = b"Hello, World!"
        encoded = self.converter._encode_ascii85(test_data)
        
        assert encoded.startswith('<~')
        assert encoded.endswith('~>')
        assert len(encoded) > len(test_data)  # Should have some overhead

    def test_ascii85_decoding_basic(self):
        """Test basic ASCII85 decoding"""
        test_data = b"Hello, World!"
        encoded = self.converter._encode_ascii85(test_data)
        decoded = self.converter._decode_ascii85(encoded)
        
        assert decoded == test_data

    def test_ascii85_roundtrip(self):
        """Test ASCII85 encode/decode roundtrip"""
        test_data = b"This is a longer test string with various characters: 12345!@#$%^&*()"
        encoded = self.converter._encode_ascii85(test_data)
        decoded = self.converter._decode_ascii85(encoded)
        
        assert decoded == test_data

    def test_ascii85_empty_data(self):
        """Test ASCII85 with empty data"""
        encoded = self.converter._encode_ascii85(b"")
        decoded = self.converter._decode_ascii85(encoded)
        
        assert decoded == b""

    @patch('cv2.VideoCapture')
    def test_convert_success(self, mock_cv2):
        """Test successful ASCII85 conversion"""
        # Mock video capture
        mock_cap = Mock()
        mock_cap.get.side_effect = lambda prop: {
            'cv2.CAP_PROP_FRAME_WIDTH': 640,
            'cv2.CAP_PROP_FRAME_HEIGHT': 480,
            'cv2.CAP_PROP_FPS': 30.0,
            'cv2.CAP_PROP_FRAME_COUNT': 300
        }.get(str(prop), 0)
        mock_cap.read.return_value = (True, np.zeros((480, 640, 3), dtype=np.uint8))
        mock_cv2.return_value = mock_cap

        # Create test MP4 file
        test_mp4 = os.path.join(self.temp_dir, 'test.mp4')
        with open(test_mp4, 'wb') as f:
            f.write(b"fake mp4 data for testing")

        output_svg = os.path.join(self.temp_dir, 'output.svg')
        
        result = self.converter.convert(test_mp4, output_svg)
        
        assert result == output_svg
        assert os.path.exists(output_svg)
        
        # Verify SVG content structure
        with open(output_svg, 'r') as f:
            content = f.read()
        
        assert '<?xml version="1.0"' in content
        assert 'xmlns:video="http://example.org/video/2024"' in content
        assert 'encoding="ascii85"' in content
        assert '<![CDATA[' in content

    def test_convert_invalid_input(self):
        """Test conversion with invalid input"""
        with pytest.raises(FileNotFoundError):
            self.converter.convert('nonexistent.mp4', 'output.svg')


class TestPolyglotConverter:
    """Test Polyglot converter functionality"""

    def setup_method(self):
        self.converter = PolyglotSVGConverter()
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_boundary_generation(self):
        """Test that boundary is properly generated"""
        assert self.converter.boundary.startswith('POLYGLOT_BOUNDARY_')
        assert len(self.converter.boundary) > 20  # Should be reasonably long

    def test_encode_decode_comment(self):
        """Test encoding/decoding for SVG comments"""
        test_data = b"Test binary data with \x00\x01\x02 null bytes"
        encoded = self.converter._encode_for_svg_comment(test_data)
        decoded = self.converter._decode_from_svg_comment(encoded)
        
        assert decoded == test_data

    @patch('cv2.VideoCapture')
    def test_convert_mp4_only(self, mock_cv2):
        """Test polyglot conversion with MP4 only"""
        # Mock video capture
        mock_cap = Mock()
        mock_cap.get.side_effect = lambda prop: {
            'cv2.CAP_PROP_FRAME_WIDTH': 320,
            'cv2.CAP_PROP_FRAME_HEIGHT': 240,
            'cv2.CAP_PROP_FPS': 24.0,
            'cv2.CAP_PROP_FRAME_COUNT': 120
        }.get(str(prop), 0)
        mock_cap.read.return_value = (True, np.zeros((240, 320, 3), dtype=np.uint8))
        mock_cv2.return_value = mock_cap

        # Create test files
        test_mp4 = os.path.join(self.temp_dir, 'test.mp4')
        with open(test_mp4, 'wb') as f:
            f.write(b"test mp4 content")

        output_svg = os.path.join(self.temp_dir, 'output.svg')
        
        result = self.converter.convert(test_mp4, output_svg)
        
        assert result == output_svg
        assert os.path.exists(output_svg)
        
        # Verify polyglot structure
        with open(output_svg, 'r') as f:
            content = f.read()
        
        assert self.converter.boundary in content
        assert '<!--MP4_DATA' in content
        assert 'MP4_DATA-->' in content


class TestVectorConverter:
    """Test Vector converter functionality"""

    def setup_method(self):
        self.converter = SVGVectorFrameConverter()
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_contour_to_path_basic(self):
        """Test converting contour to SVG path"""
        # Simple triangle contour
        contour = np.array([[[10, 10]], [[50, 10]], [[30, 40]]], dtype=np.int32)
        path = self.converter._contour_to_path(contour)
        
        assert path.startswith('M 10,10')
        assert 'L 50,10' in path
        assert 'L 30,40' in path
        assert path.endswith('Z')

    def test_contour_to_path_empty(self):
        """Test converting empty contour"""
        contour = np.array([[]], dtype=np.int32).reshape(0, 1, 2)
        path = self.converter._contour_to_path(contour)
        
        assert path == ""

    @patch('cv2.VideoCapture')
    @patch('cv2.findContours')
    @patch('cv2.Canny')
    def test_frame_to_svg_paths(self, mock_canny, mock_contours, mock_cv2):
        """Test converting frame to SVG paths"""
        # Mock frame processing
        mock_canny.return_value = np.zeros((100, 100), dtype=np.uint8)
        mock_contours.return_value = (
            [np.array([[[10, 10]], [[50, 10]], [[30, 40]]], dtype=np.int32)],
            None
        )
        
        test_frame = np.zeros((100, 100, 3), dtype=np.uint8)
        paths = self.converter._frame_to_svg_paths(test_frame, 50)
        
        assert isinstance(paths, list)

    def test_extract_not_supported(self):
        """Test that vector extraction returns False (not supported)"""
        result = self.converter.extract('dummy.svg', 'output.mp4')
        assert result is False


class TestQRCodeConverter:
    """Test QR Code converter functionality"""

    def setup_method(self):
        self.converter = QRCodeSVGConverter(chunk_size=100)  # Small chunks for testing
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch('cv2.VideoCapture')
    @patch('qrcode.QRCode')
    def test_convert_basic(self, mock_qr_class, mock_cv2):
        """Test basic QR code conversion"""
        # Mock video capture
        mock_cap = Mock()
        mock_cap.get.side_effect = lambda prop: {
            'cv2.CAP_PROP_FRAME_WIDTH': 400,
            'cv2.CAP_PROP_FRAME_HEIGHT': 300,
            'cv2.CAP_PROP_FPS': 15.0,
            'cv2.CAP_PROP_FRAME_COUNT': 75
        }.get(str(prop), 0)
        mock_cv2.return_value = mock_cap

        # Mock QR code generation
        mock_qr = Mock()
        mock_img = Mock()
        mock_img.save = Mock()
        mock_qr.make_image.return_value = mock_img
        mock_qr_class.return_value = mock_qr

        # Create test MP4
        test_mp4 = os.path.join(self.temp_dir, 'test.mp4')
        with open(test_mp4, 'wb') as f:
            f.write(b"A" * 250)  # Will create 3 chunks with chunk_size=100

        output_svg = os.path.join(self.temp_dir, 'output.svg')
        
        result = self.converter.convert(test_mp4, output_svg)
        
        assert result == output_svg
        assert os.path.exists(output_svg)

    def test_generate_extraction_script(self):
        """Test extraction script generation"""
        script = self.converter._generate_extraction_script('test.svg', 'output.mp4')
        
        assert 'import json' in script
        assert 'import base64' in script
        assert 'test.svg' in script
        assert 'output.mp4' in script


class TestHybridConverter:
    """Test Hybrid converter functionality"""

    def setup_method(self):
        self.converter = HybridSVGConverter()
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_format_detection_polyglot(self):
        """Test polyglot format detection"""
        test_svg = os.path.join(self.temp_dir, 'test.svg')
        with open(test_svg, 'w') as f:
            f.write('<!--POLYGLOT_BOUNDARY_abc123-->')
        
        # Use extract to test detection
        with patch.object(self.converter.polyglot, 'extract', return_value=True):
            result = self.converter.extract(test_svg, 'output.mp4')
            assert result is True

    def test_format_detection_ascii85(self):
        """Test ASCII85 format detection"""
        test_svg = os.path.join(self.temp_dir, 'test.svg')
        with open(test_svg, 'w') as f:
            f.write('<video:data encoding="ascii85">')
        
        with patch.object(self.converter.ascii85, 'extract', return_value=True):
            result = self.converter.extract(test_svg, 'output.mp4')
            assert result is True

    def test_format_detection_unknown(self):
        """Test unknown format detection"""
        test_svg = os.path.join(self.temp_dir, 'test.svg')
        with open(test_svg, 'w') as f:
            f.write('<svg><rect/></svg>')
        
        result = self.converter.extract(test_svg, 'output.mp4')
        assert result is False


class TestIntegration:
    """Integration tests across converters"""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch('cv2.VideoCapture')
    def test_ascii85_full_roundtrip(self, mock_cv2):
        """Test full ASCII85 encode/decode roundtrip"""
        # Mock video capture
        mock_cap = Mock()
        mock_cap.get.side_effect = lambda prop: 640 if 'WIDTH' in str(prop) else 480 if 'HEIGHT' in str(prop) else 30.0 if 'FPS' in str(prop) else 300
        mock_cap.read.return_value = (True, np.zeros((480, 640, 3), dtype=np.uint8))
        mock_cv2.return_value = mock_cap

        converter = ASCII85SVGConverter()
        
        # Create test MP4
        test_data = b"Test video data for roundtrip validation"
        test_mp4 = os.path.join(self.temp_dir, 'test.mp4')
        with open(test_mp4, 'wb') as f:
            f.write(test_data)

        # Convert to SVG
        output_svg = os.path.join(self.temp_dir, 'output.svg')
        converter.convert(test_mp4, output_svg)
        
        # Extract back to MP4
        extracted_mp4 = os.path.join(self.temp_dir, 'extracted.mp4')
        success = converter.extract(output_svg, extracted_mp4)
        
        assert success
        assert os.path.exists(extracted_mp4)
        
        # Verify data integrity
        with open(extracted_mp4, 'rb') as f:
            extracted_data = f.read()
        
        assert extracted_data == test_data
