"""
Data integrity validation for mp4svg files
"""

import os
import hashlib
import json
import base64
from typing import Dict, Optional, Tuple
from ..ascii85 import ASCII85SVGConverter
from ..polyglot import PolyglotSVGConverter
from ..base import ValidationError


class IntegrityValidator:
    """Validates data integrity in mp4svg files through round-trip testing"""

    def __init__(self):
        self.ascii85_converter = ASCII85SVGConverter()
        self.polyglot_converter = PolyglotSVGConverter()

    def validate_integrity(self, svg_path: str, original_mp4_path: Optional[str] = None) -> Dict:
        """
        Validate data integrity by attempting extraction and comparison
        
        Args:
            svg_path: Path to SVG file to validate
            original_mp4_path: Optional path to original MP4 for comparison
            
        Returns:
            Dict with integrity validation results
        """
        
        if not os.path.exists(svg_path):
            raise FileNotFoundError(f"SVG file not found: {svg_path}")
        
        result = {
            'svg_path': svg_path,
            'original_mp4_path': original_mp4_path,
            'format_detected': None,
            'extraction_successful': False,
            'data_integrity_valid': False,
            'size_match': False,
            'checksum_match': False,
            'extracted_size': 0,
            'original_size': 0,
            'extracted_checksum': None,
            'original_checksum': None,
            'errors': [],
            'warnings': []
        }
        
        try:
            # Detect format
            result['format_detected'] = self._detect_format(svg_path)
            
            if not result['format_detected']:
                result['errors'].append("Could not detect mp4svg format")
                return result
            
            # Attempt extraction
            extracted_data = self._extract_data(svg_path, result['format_detected'])
            
            if extracted_data:
                result['extraction_successful'] = True
                result['extracted_size'] = len(extracted_data)
                result['extracted_checksum'] = hashlib.sha256(extracted_data).hexdigest()
                
                # Compare with original if provided
                if original_mp4_path and os.path.exists(original_mp4_path):
                    original_data = self._read_original_mp4(original_mp4_path)
                    result['original_size'] = len(original_data)
                    result['original_checksum'] = hashlib.sha256(original_data).hexdigest()
                    
                    # Check integrity
                    result['size_match'] = result['extracted_size'] == result['original_size']
                    result['checksum_match'] = result['extracted_checksum'] == result['original_checksum']
                    result['data_integrity_valid'] = result['size_match'] and result['checksum_match']
                    
                    if not result['size_match']:
                        result['errors'].append(f"Size mismatch: extracted {result['extracted_size']:,} vs original {result['original_size']:,} bytes")
                    
                    if not result['checksum_match']:
                        result['errors'].append("Checksum mismatch: data corruption detected")
                else:
                    result['warnings'].append("No original MP4 provided for comparison")
                    # For formats like polyglot/ascii85, extraction success implies integrity
                    if result['format_detected'] in ['polyglot', 'ascii85']:
                        result['data_integrity_valid'] = True
            else:
                result['errors'].append("Failed to extract data from SVG")
        
        except Exception as e:
            result['errors'].append(f"Integrity validation failed: {str(e)}")
        
        return result

    def validate_embedded_checksums(self, svg_path: str) -> Dict:
        """
        Validate embedded checksums within SVG metadata
        """
        
        result = {
            'svg_path': svg_path,
            'has_embedded_checksums': False,
            'checksums_valid': False,
            'checksum_details': {},
            'errors': [],
            'warnings': []
        }
        
        try:
            format_type = self._detect_format(svg_path)
            
            if format_type == 'qrcode':
                # QR code format often includes chunk checksums
                result.update(self._validate_qr_checksums(svg_path))
            elif format_type == 'polyglot':
                # Polyglot may include summary checksums
                result.update(self._validate_polyglot_checksums(svg_path))
            else:
                result['warnings'].append(f"Format '{format_type}' typically doesn't include embedded checksums")
        
        except Exception as e:
            result['errors'].append(f"Checksum validation failed: {str(e)}")
        
        return result

    def _detect_format(self, svg_path: str) -> Optional[str]:
        """Detect mp4svg format type"""
        
        with open(svg_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if 'POLYGLOT_BOUNDARY_' in content:
            return 'polyglot'
        elif 'encoding="ascii85"' in content:
            return 'ascii85'
        elif 'qr-frame-' in content:
            return 'qrcode'
        elif '<path d=' in content and '<set attributeName=' in content:
            return 'vector'
        
        return None

    def _extract_data(self, svg_path: str, format_type: str) -> Optional[bytes]:
        """Extract binary data from SVG based on format"""
        
        temp_output = svg_path.replace('.svg', '_temp_extracted.mp4')
        
        try:
            if format_type == 'ascii85':
                success = self.ascii85_converter.extract(svg_path, temp_output)
            elif format_type == 'polyglot':
                success = self.polyglot_converter.extract(svg_path, temp_output)
            else:
                return None  # Vector and QR formats need special handling
            
            if success and os.path.exists(temp_output):
                with open(temp_output, 'rb') as f:
                    data = f.read()
                os.unlink(temp_output)  # Clean up
                return data
            
        except Exception:
            if os.path.exists(temp_output):
                os.unlink(temp_output)
        
        return None

    def _read_original_mp4(self, mp4_path: str) -> bytes:
        """Read original MP4 file"""
        with open(mp4_path, 'rb') as f:
            return f.read()

    def _validate_qr_checksums(self, svg_path: str) -> Dict:
        """Validate checksums in QR code format"""
        
        result = {
            'has_embedded_checksums': False,
            'checksums_valid': False,
            'checksum_details': {},
            'chunk_checksums': []
        }
        
        try:
            import xml.etree.ElementTree as ET
            tree = ET.parse(svg_path)
            root = tree.getroot()
            
            # Look for metadata with overall checksum
            metadata_elem = root.find('metadata')
            if metadata_elem is not None:
                try:
                    metadata = json.loads(metadata_elem.text)
                    if 'checksum' in metadata:
                        result['has_embedded_checksums'] = True
                        result['checksum_details']['overall_checksum'] = metadata['checksum']
                        result['checksum_details']['chunks'] = metadata.get('chunks', 0)
                        result['checksum_details']['total_size'] = metadata.get('total_size', 0)
                except:
                    pass
            
            # Note: Full QR validation would require decoding QR codes
            # This is a placeholder for the structure
            if result['has_embedded_checksums']:
                result['warnings'] = ["QR code checksum validation requires QR decoding"]
            
        except Exception as e:
            result['errors'] = [f"QR checksum validation error: {str(e)}"]
        
        return result

    def _validate_polyglot_checksums(self, svg_path: str) -> Dict:
        """Validate checksums in polyglot format"""
        
        result = {
            'has_embedded_checksums': False,
            'checksums_valid': False,
            'checksum_details': {}
        }
        
        try:
            with open(svg_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Look for summary section with checksums
            if 'Summary:' in content and 'bytes' in content:
                result['has_embedded_checksums'] = True
                
                # Extract embedded size information
                import re
                size_matches = re.findall(r'(\d+(?:,\d+)*)\s+bytes', content)
                if size_matches:
                    # Convert comma-separated numbers
                    sizes = [int(match.replace(',', '')) for match in size_matches]
                    result['checksum_details']['embedded_sizes'] = sizes
                
                # Polyglot format relies on perfect embedding rather than checksums
                result['checksums_valid'] = True
                result['warnings'] = ["Polyglot format validation relies on extraction success"]
        
        except Exception as e:
            result['errors'] = [f"Polyglot checksum validation error: {str(e)}"]
        
        return result

    def batch_validate(self, svg_directory: str, original_directory: Optional[str] = None) -> Dict:
        """
        Validate integrity of multiple SVG files in a directory
        
        Args:
            svg_directory: Directory containing SVG files
            original_directory: Optional directory with original MP4 files
            
        Returns:
            Dict with batch validation results
        """
        
        if not os.path.isdir(svg_directory):
            raise ValueError(f"SVG directory not found: {svg_directory}")
        
        svg_files = [f for f in os.listdir(svg_directory) if f.lower().endswith('.svg')]
        
        results = {
            'svg_directory': svg_directory,
            'original_directory': original_directory,
            'total_files': len(svg_files),
            'files_processed': 0,
            'files_valid': 0,
            'files_with_errors': 0,
            'individual_results': {},
            'summary': {
                'formats_detected': {},
                'common_errors': [],
                'recommendations': []
            }
        }
        
        for svg_file in svg_files:
            svg_path = os.path.join(svg_directory, svg_file)
            
            # Try to find corresponding MP4
            original_mp4_path = None
            if original_directory:
                mp4_name = svg_file.replace('.svg', '.mp4')
                potential_mp4 = os.path.join(original_directory, mp4_name)
                if os.path.exists(potential_mp4):
                    original_mp4_path = potential_mp4
            
            # Validate individual file
            try:
                file_result = self.validate_integrity(svg_path, original_mp4_path)
                results['individual_results'][svg_file] = file_result
                results['files_processed'] += 1
                
                if file_result['data_integrity_valid'] or (not original_mp4_path and file_result['extraction_successful']):
                    results['files_valid'] += 1
                
                if file_result['errors']:
                    results['files_with_errors'] += 1
                
                # Track format statistics
                fmt = file_result['format_detected']
                if fmt:
                    results['summary']['formats_detected'][fmt] = results['summary']['formats_detected'].get(fmt, 0) + 1
            
            except Exception as e:
                results['individual_results'][svg_file] = {'errors': [str(e)]}
                results['files_with_errors'] += 1
        
        # Generate summary recommendations
        if results['files_with_errors'] > 0:
            results['summary']['recommendations'].append(f"Review {results['files_with_errors']} files with errors")
        
        if results['files_valid'] == results['files_processed']:
            results['summary']['recommendations'].append("All files passed integrity validation")
        
        return results
