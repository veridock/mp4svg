"""
QR Code converter for MP4 to SVG
Stores data as QR codes embedded in SVG frames (memvid-inspired)
"""

import os
import json
import hashlib
import base64
from io import BytesIO
from typing import List
import qrcode
from PIL import Image
from lxml import etree
from .base import BaseConverter, EncodingError, DecodingError


class QRCodeSVGConverter(BaseConverter):
    """Converts data to QR codes embedded in SVG frames (memvid-inspired)"""

    def __init__(self, chunk_size: int = 1024):
        self.chunk_size = chunk_size

    def convert(self, mp4_path: str, output_path: str, include_metadata: bool = True) -> str:
        """Convert MP4 to SVG with QR code frames"""
        
        self._validate_input(mp4_path)
        print(f"[QR] Processing {mp4_path}...")
        print(f"[QR] Chunk size: {self.chunk_size} bytes")

        try:
            # Read video data
            with open(mp4_path, 'rb') as f:
                mp4_data = f.read()

            # Split data into chunks
            chunks = [mp4_data[i:i + self.chunk_size] 
                     for i in range(0, len(mp4_data), self.chunk_size)]

            print(f"[QR] Split into {len(chunks)} chunks")

            # Get video metadata
            metadata = self._get_video_metadata(mp4_path)
            width = metadata['width']
            height = metadata['height']

            # Calculate QR grid dimensions
            qr_size = min(width, height) // 2
            grid_cols = max(1, width // qr_size)
            grid_rows = max(1, (len(chunks) + grid_cols - 1) // grid_cols)

            # Create SVG
            svg = etree.Element('svg', {
                'xmlns': 'http://www.w3.org/2000/svg',
                'xmlns:xlink': 'http://www.w3.org/1999/xlink',
                'width': str(width),
                'height': str(height),
                'viewBox': f'0 0 {width} {height}'
            })

            # Add metadata if requested
            if include_metadata:
                metadata_info = {
                    'format': 'qr_memvid',
                    'chunks': len(chunks),
                    'chunk_size': self.chunk_size,
                    'total_size': len(mp4_data),
                    'checksum': hashlib.sha256(mp4_data).hexdigest()
                }

                meta_elem = etree.SubElement(svg, 'metadata')
                meta_elem.text = json.dumps(metadata_info, indent=2)

            # Create QR codes for each chunk
            print("[QR] Generating QR codes...")
            
            for idx, chunk in enumerate(chunks):
                # Encode chunk as base64 for QR code
                chunk_b64 = base64.b64encode(chunk).decode('ascii')
                
                # Add chunk header with index and checksum
                chunk_data = {
                    'idx': idx,
                    'total': len(chunks),
                    'checksum': hashlib.md5(chunk).hexdigest()[:8],
                    'data': chunk_b64
                }
                
                qr_content = json.dumps(chunk_data, separators=(',', ':'))
                
                # Generate QR code
                qr = qrcode.QRCode(
                    version=None,  # Auto-size
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=2,
                    border=1,
                )
                qr.add_data(qr_content)
                qr.make(fit=True)
                
                # Create QR code image
                qr_img = qr.make_image(fill_color="black", back_color="white")
                
                # Calculate position
                x = (idx % grid_cols) * qr_size
                y = (idx // grid_cols) * qr_size

                # Create frame group
                frame_group = etree.SubElement(svg, 'g', {
                    'id': f'qr-frame-{idx}',
                    'transform': f'translate({x},{y})',
                    'opacity': '1' if idx == 0 else '0.1'
                })

                # Convert QR image to base64
                qr_buffer = BytesIO()
                qr_img.save(qr_buffer, format='PNG')
                qr_base64 = base64.b64encode(qr_buffer.getvalue()).decode('ascii')

                image = etree.SubElement(frame_group, 'image', {
                    'x': '0',
                    'y': '0',
                    'width': str(qr_size),
                    'height': str(qr_size),
                    'href': f'data:image/png;base64,{qr_base64}'
                })

                print(f"[QR] Chunk {idx + 1}/{len(chunks)}: {len(chunk)} bytes")

            # Save SVG
            tree = etree.ElementTree(svg)
            tree.write(output_path, encoding='utf-8', xml_declaration=True)

            print(f"[QR] Created: {output_path}")
            print(f"[QR] Original: {len(mp4_data):,} bytes")
            print(f"[QR] QR codes: {len(chunks)}")
            print(f"[QR] Grid: {grid_cols}x{grid_rows}")

            return output_path
            
        except Exception as e:
            raise EncodingError(f"QR code conversion failed: {str(e)}")

    def extract(self, svg_path: str, output_mp4: str) -> bool:
        """Extract MP4 from QR code SVG"""
        
        print("[QR] Note: QR code extraction requires external QR code reader")
        print("[QR] This method provides instructions for manual extraction")
        
        try:
            # Parse SVG to get metadata
            tree = etree.parse(svg_path)
            root = tree.getroot()
            
            # Look for metadata
            metadata_elem = root.find('metadata')
            if metadata_elem is not None:
                try:
                    metadata = json.loads(metadata_elem.text)
                    print(f"[QR] Found metadata: {metadata['chunks']} chunks expected")
                    print(f"[QR] Original size: {metadata['total_size']:,} bytes")
                    print(f"[QR] Checksum: {metadata['checksum']}")
                except:
                    pass

            # Count QR frames
            qr_frames = root.findall(".//g[@id]")
            qr_count = len([g for g in qr_frames if g.get('id', '').startswith('qr-frame-')])
            
            print(f"[QR] Found {qr_count} QR code frames in SVG")
            print(f"[QR] To extract:")
            print(f"[QR] 1. Use QR code scanner app on each frame")
            print(f"[QR] 2. Decode JSON from each QR code")
            print(f"[QR] 3. Sort by 'idx' field and concatenate 'data' fields")
            print(f"[QR] 4. Base64 decode the result to get MP4")
            
            # For demonstration, create extraction script
            script_path = svg_path.replace('.svg', '_extract.py')
            extraction_script = self._generate_extraction_script(svg_path, output_mp4)
            
            with open(script_path, 'w') as f:
                f.write(extraction_script)
                
            print(f"[QR] Created extraction script: {script_path}")
            print(f"[QR] Run: python {script_path}")
            
            return True
            
        except Exception as e:
            raise DecodingError(f"QR code analysis failed: {str(e)}")

    def _generate_extraction_script(self, svg_path: str, output_mp4: str) -> str:
        """Generate Python script for QR code extraction"""
        
        return f'''#!/usr/bin/env python3
"""
QR Code extraction script for {svg_path}
Requirements: pip install qrcode pillow pyzbar opencv-python
"""

import json
import base64
import hashlib
from xml.etree import ElementTree as ET
import cv2
from pyzbar import pyzbar


def extract_qr_codes_from_svg():
    """Extract QR codes from SVG and reconstruct MP4"""
    
    # Parse SVG
    tree = ET.parse('{svg_path}')
    root = tree.getroot()
    
    # Find all QR code images
    images = root.findall('.//{{{root.nsmap[None]}}}image')
    
    chunks = {{}}
    
    for img in images:
        href = img.get('href', '')
        if not href.startswith('data:image/png;base64,'):
            continue
            
        # Decode base64 image
        image_b64 = href.split(',', 1)[1]
        image_data = base64.b64decode(image_b64)
        
        # Save temporary image
        with open('temp_qr.png', 'wb') as f:
            f.write(image_data)
        
        # Read QR code
        image = cv2.imread('temp_qr.png')
        qr_codes = pyzbar.decode(image)
        
        for qr in qr_codes:
            try:
                data = json.loads(qr.data.decode('utf-8'))
                idx = data['idx']
                chunks[idx] = data
                print(f"Decoded chunk {{idx}}/{{data.get('total', '?')}}")
            except:
                continue
    
    if not chunks:
        print("No QR codes found or decoded")
        return False
    
    # Sort chunks and reconstruct data
    sorted_chunks = [chunks[i] for i in sorted(chunks.keys())]
    
    # Concatenate base64 data
    full_b64 = ''.join(chunk['data'] for chunk in sorted_chunks)
    
    # Decode to binary
    mp4_data = base64.b64decode(full_b64)
    
    # Verify checksum if available
    calculated_checksum = hashlib.sha256(mp4_data).hexdigest()
    print(f"Reconstructed {{len(mp4_data):,}} bytes")
    print(f"Checksum: {{calculated_checksum}}")
    
    # Write MP4 file
    with open('{output_mp4}', 'wb') as f:
        f.write(mp4_data)
    
    print(f"Extracted MP4 to: {output_mp4}")
    return True


if __name__ == '__main__':
    extract_qr_codes_from_svg()
'''
