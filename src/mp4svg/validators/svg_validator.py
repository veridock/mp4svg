"""
SVG format validation for mp4svg generated files
"""

import os
import xml.etree.ElementTree as ET
from lxml import etree
from typing import Dict, List, Optional, Tuple
from ..base import ValidationError


class SVGValidator:
    """Validates SVG files for well-formedness and mp4svg compliance"""

    def __init__(self):
        self.errors = []
        self.warnings = []

    def validate_svg_file(self, svg_path: str) -> Dict:
        """
        Validate SVG file and return comprehensive report
        
        Returns:
            Dict with validation results including errors, warnings, and metadata
        """
        self.errors = []
        self.warnings = []
        
        if not os.path.exists(svg_path):
            raise FileNotFoundError(f"SVG file not found: {svg_path}")
        
        result = {
            'file_path': svg_path,
            'file_size': os.path.getsize(svg_path),
            'is_valid': False,
            'is_well_formed': False,
            'detected_format': None,
            'metadata': {},
            'errors': [],
            'warnings': [],
            'recommendations': []
        }
        
        try:
            # Test XML well-formedness
            result['is_well_formed'] = self._check_xml_wellformed(svg_path)
            
            # Parse SVG content
            content = self._read_svg_content(svg_path)
            root = self._parse_svg_safely(svg_path)
            
            if root is not None:
                # Detect mp4svg format
                result['detected_format'] = self._detect_format(content, root)
                
                # Extract metadata
                result['metadata'] = self._extract_metadata(root, result['detected_format'])
                
                # Validate SVG structure
                self._validate_svg_structure(root)
                
                # Format-specific validation
                if result['detected_format']:
                    self._validate_format_specific(content, root, result['detected_format'])
                
                # Check for common issues
                self._check_common_issues(content, root)
                
                # Generate recommendations
                self._generate_recommendations(result)
            
            result['errors'] = self.errors
            result['warnings'] = self.warnings
            result['is_valid'] = len(self.errors) == 0
            
        except Exception as e:
            self.errors.append(f"Validation failed: {str(e)}")
            result['errors'] = self.errors
            
        return result

    def _check_xml_wellformed(self, svg_path: str) -> bool:
        """Check if SVG is well-formed XML"""
        try:
            etree.parse(svg_path)
            return True
        except etree.XMLSyntaxError as e:
            self.errors.append(f"XML syntax error: {str(e)}")
            return False
        except Exception as e:
            self.errors.append(f"XML parsing error: {str(e)}")
            return False

    def _read_svg_content(self, svg_path: str) -> str:
        """Read SVG file content safely"""
        try:
            with open(svg_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            try:
                with open(svg_path, 'r', encoding='latin-1') as f:
                    content = f.read()
                    self.warnings.append("File encoding is not UTF-8")
                    return content
            except Exception as e:
                raise ValidationError(f"Cannot read file: {str(e)}")

    def _parse_svg_safely(self, svg_path: str) -> Optional[ET.Element]:
        """Parse SVG with error handling"""
        try:
            tree = ET.parse(svg_path)
            return tree.getroot()
        except ET.ParseError as e:
            self.errors.append(f"SVG parsing error: {str(e)}")
            return None

    def _detect_format(self, content: str, root: ET.Element) -> Optional[str]:
        """Detect mp4svg format type"""
        
        # Check for polyglot format
        if 'POLYGLOT_BOUNDARY_' in content:
            return 'polyglot'
        
        # Check for ASCII85 format
        if 'encoding="ascii85"' in content:
            return 'ascii85'
        
        # Check for QR code format
        if 'qr-frame-' in content:
            return 'qrcode'
        
        # Check for vector format
        if root.find('.//path[@d]') is not None and root.find('.//set[@attributeName]') is not None:
            return 'vector'
        
        # Check for hybrid format indicators
        if any(fmt in content for fmt in ['polyglot', 'ascii85', 'qrcode', 'vector']):
            return 'hybrid'
        
        return None

    def _extract_metadata(self, root: ET.Element, format_type: str) -> Dict:
        """Extract metadata from SVG"""
        metadata = {
            'width': root.get('width'),
            'height': root.get('height'),
            'viewBox': root.get('viewBox'),
            'title': None,
            'description': None
        }
        
        # Extract title and description
        title_elem = root.find('title')
        if title_elem is not None:
            metadata['title'] = title_elem.text
        
        desc_elem = root.find('desc')
        if desc_elem is not None:
            metadata['description'] = desc_elem.text
        
        # Format-specific metadata
        if format_type == 'ascii85':
            video_ns = {'video': 'http://example.org/video/2024'}
            video_data = root.find('.//video:data', video_ns)
            if video_data is not None:
                metadata.update({
                    'encoding': video_data.get('encoding'),
                    'originalSize': video_data.get('originalSize'),
                    'fps': video_data.get('fps'),
                    'frames': video_data.get('frames')
                })
        
        elif format_type == 'qrcode':
            metadata_elem = root.find('metadata')
            if metadata_elem is not None:
                try:
                    import json
                    qr_metadata = json.loads(metadata_elem.text)
                    metadata.update(qr_metadata)
                except:
                    pass
        
        return metadata

    def _validate_svg_structure(self, root: ET.Element) -> None:
        """Validate basic SVG structure"""
        
        # Check root element
        if root.tag != '{http://www.w3.org/2000/svg}svg' and root.tag != 'svg':
            self.errors.append("Root element is not <svg>")
        
        # Check required attributes
        if not root.get('width') and not root.get('viewBox'):
            self.warnings.append("SVG missing width attribute and viewBox")
        
        if not root.get('height') and not root.get('viewBox'):
            self.warnings.append("SVG missing height attribute and viewBox")
        
        # Check for xmlns
        xmlns = root.get('xmlns') or root.get('{http://www.w3.org/2000/xmlns/}xmlns')
        if xmlns != 'http://www.w3.org/2000/svg':
            self.warnings.append("SVG namespace not properly declared")

    def _validate_format_specific(self, content: str, root: ET.Element, format_type: str) -> None:
        """Validate format-specific requirements"""
        
        if format_type == 'ascii85':
            self._validate_ascii85_format(root)
        elif format_type == 'polyglot':
            self._validate_polyglot_format(content)
        elif format_type == 'qrcode':
            self._validate_qrcode_format(root)
        elif format_type == 'vector':
            self._validate_vector_format(root)

    def _validate_ascii85_format(self, root: ET.Element) -> None:
        """Validate ASCII85 format specific requirements"""
        
        # Check for video namespace
        video_ns = {'video': 'http://example.org/video/2024'}
        video_data = root.find('.//video:data', video_ns)
        
        if video_data is None:
            self.errors.append("ASCII85 format: video:data element not found")
            return
        
        # Check encoding attribute
        if video_data.get('encoding') != 'ascii85':
            self.errors.append("ASCII85 format: incorrect encoding attribute")
        
        # Check for required attributes
        required_attrs = ['originalSize', 'fps', 'frames']
        for attr in required_attrs:
            if not video_data.get(attr):
                self.warnings.append(f"ASCII85 format: missing {attr} attribute")
        
        # Validate CDATA content
        if not video_data.text or not video_data.text.strip():
            self.errors.append("ASCII85 format: empty video data")

    def _validate_polyglot_format(self, content: str) -> None:
        """Validate polyglot format specific requirements"""
        
        # Check for boundary markers
        if 'MP4_DATA' not in content:
            self.errors.append("Polyglot format: MP4_DATA markers not found")
        
        # Check for proper comment structure
        if '<!--MP4_DATA' not in content or 'MP4_DATA-->' not in content:
            self.errors.append("Polyglot format: malformed MP4_DATA comments")

    def _validate_qrcode_format(self, root: ET.Element) -> None:
        """Validate QR code format specific requirements"""
        
        # Check for QR frame groups
        qr_frames = [elem for elem in root.iter() if elem.get('id', '').startswith('qr-frame-')]
        
        if not qr_frames:
            self.errors.append("QR format: no QR frames found")
        
        # Check for images in frames
        for frame in qr_frames[:5]:  # Check first 5 frames
            images = frame.findall('.//image')
            if not images:
                self.warnings.append(f"QR frame {frame.get('id')}: no images found")

    def _validate_vector_format(self, root: ET.Element) -> None:
        """Validate vector format specific requirements"""
        
        # Check for path elements
        paths = root.findall('.//path')
        if not paths:
            self.warnings.append("Vector format: no path elements found")
        
        # Check for animation elements
        animations = root.findall('.//set') + root.findall('.//animate')
        if not animations:
            self.warnings.append("Vector format: no animation elements found")

    def _check_common_issues(self, content: str, root: ET.Element) -> None:
        """Check for common issues in mp4svg files"""
        
        # Check file size
        content_size = len(content.encode('utf-8'))
        if content_size > 100 * 1024 * 1024:  # 100MB
            self.warnings.append(f"Large file size: {content_size:,} bytes")
        
        # Check for script elements
        scripts = root.findall('.//script')
        for script in scripts:
            if script.text and len(script.text) > 10000:
                self.warnings.append("Large JavaScript content detected")
        
        # Check for embedded images
        images = root.findall('.//image')
        for img in images:
            href = img.get('href', '')
            if href.startswith('data:') and len(href) > 1000000:  # 1MB
                self.warnings.append("Large embedded image detected")

    def _generate_recommendations(self, result: Dict) -> None:
        """Generate recommendations based on validation results"""
        
        recommendations = []
        
        if not result['is_well_formed']:
            recommendations.append("Fix XML syntax errors before use")
        
        if result['detected_format'] is None:
            recommendations.append("File may not be a valid mp4svg format")
        
        if result['file_size'] > 50 * 1024 * 1024:  # 50MB
            recommendations.append("Consider using compression or different encoding method")
        
        if self.warnings:
            recommendations.append("Review warnings for potential improvements")
        
        result['recommendations'] = recommendations
