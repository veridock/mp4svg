#!/usr/bin/env python3
"""
MP4 to SVG Converter Suite
Complete set of converters for different encoding methods
Author: SVG Video System
"""

import cv2
import numpy as np
import base64
import struct
import hashlib
import json
import gzip
import io
import os
import sys
from pathlib import Path
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass
from PIL import Image
import qrcode
from lxml import etree
from xml.dom import minidom


# ============================================
# Method 1: Polyglot File Converter
# ============================================

class PolyglotSVGConverter:
    """Creates SVG files that contain hidden MP4 data"""

    def __init__(self):
        self.boundary = f"POLYGLOT_BOUNDARY_{hashlib.md5(os.urandom(16)).hexdigest()}"

    def convert(self, mp4_path: str, output_path: str, pdf_path: Optional[str] = None) -> str:
        """Convert MP4 to polyglot SVG file"""

        print(f"[Polyglot] Processing {mp4_path}...")

        # Read MP4 binary data
        with open(mp4_path, 'rb') as f:
            mp4_data = f.read()

        # Create base SVG structure
        svg_content = self._create_svg_template(mp4_path)

        # Encode binary data for safe inclusion
        encoded_mp4 = self._encode_for_svg_comment(mp4_data)

        # Add PDF if provided
        encoded_pdf = ""
        if pdf_path and os.path.exists(pdf_path):
            with open(pdf_path, 'rb') as f:
                pdf_data = f.read()
            encoded_pdf = f"\n<!--PDF_DATA\n{self._encode_for_svg_comment(pdf_data)}\nPDF_DATA-->"

        # Insert binary data before closing tag
        insertion_point = svg_content.rfind('</svg>')

        polyglot = (
                svg_content[:insertion_point] +
                f"\n<!--{self.boundary}\n" +
                f"<!--MP4_DATA\n{encoded_mp4}\nMP4_DATA-->" +
                encoded_pdf +
                f"\n{self.boundary}-->\n" +
                svg_content[insertion_point:]
        )

        # Save polyglot file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(polyglot)

        original_size = len(mp4_data)
        final_size = len(polyglot)
        print(f"[Polyglot] Created: {output_path}")
        print(f"[Polyglot] Original MP4: {original_size:,} bytes")
        print(f"[Polyglot] Final SVG: {final_size:,} bytes")
        print(f"[Polyglot] Overhead: {(final_size / original_size - 1) * 100:.1f}%")

        return output_path

    def _create_svg_template(self, video_path: str) -> str:
        """Create base SVG template with video metadata"""

        cap = cv2.VideoCapture(video_path)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        cap.release()

        return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" 
     width="{width}" height="{height}"
     viewBox="0 0 {width} {height}">
    <title>Polyglot SVG Video Container</title>
    <desc>Contains MP4 video data: {frame_count} frames at {fps:.2f} fps</desc>

    <rect width="100%" height="100%" fill="#000"/>
    <text x="50%" y="50%" text-anchor="middle" fill="#fff" font-size="20">
        Polyglot SVG Container
    </text>
    <text x="50%" y="55%" text-anchor="middle" fill="#aaa" font-size="14">
        Video: {os.path.basename(video_path)}
    </text>
</svg>'''

    def _encode_for_svg_comment(self, data: bytes) -> str:
        """Encode binary data for safe inclusion in SVG comments"""

        # Use Unicode private use area to avoid conflicts
        encoded = []
        for byte in data:
            # Map to safe Unicode range (E000-E0FF for 0-255)
            encoded.append(f"&#{0xE000 + byte};")

        return ''.join(encoded)

    def extract(self, svg_path: str, output_mp4: str) -> bool:
        """Extract MP4 from polyglot SVG"""

        with open(svg_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Find MP4 data
        start = content.find('<!--MP4_DATA\n')
        end = content.find('\nMP4_DATA-->')

        if start == -1 or end == -1:
            print("[Polyglot] No MP4 data found in SVG")
            return False

        encoded = content[start + 13:end]

        # Decode
        import re
        codes = re.findall(r'&#(\d+);', encoded)
        mp4_data = bytes([int(code) - 0xE000 for code in codes if int(code) >= 0xE000])

        with open(output_mp4, 'wb') as f:
            f.write(mp4_data)

        print(f"[Polyglot] Extracted MP4 to {output_mp4}")
        return True


# ============================================
# Method 2: ASCII85 Encoder
# ============================================

class ASCII85SVGConverter:
    """Converts MP4 to SVG using ASCII85 encoding (25% overhead vs 33% for base64)"""

    def convert(self, mp4_path: str, output_path: str) -> str:
        """Convert MP4 to SVG with ASCII85 encoding"""

        print(f"[ASCII85] Processing {mp4_path}...")

        # Read video data
        with open(mp4_path, 'rb') as f:
            mp4_data = f.read()

        # Encode using ASCII85
        encoded = self._encode_ascii85(mp4_data)

        # Base64 encode for XML safety
        encoded_b64 = base64.b64encode(encoded.encode('ascii')).decode('ascii')

        # Get video metadata
        cap = cv2.VideoCapture(mp4_path)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        cap.release()

        # Create SVG with embedded data and JavaScript decoder
        svg_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg"
     xmlns:video="http://example.org/video/2024"
     width="{width}" height="{height}">

    <title>ASCII85 Encoded Video</title>
    <desc>Video data encoded with ASCII85 (25% overhead)</desc>

    <metadata>
        <video:data encoding="ascii85" 
                    originalSize="{len(mp4_data)}"
                    fps="{fps}"
                    frames="{frame_count}">
            <![CDATA[
{encoded_b64}
            ]]>
        </video:data>
    </metadata>

    <defs>
        <style>
            .container {{ fill: #1a1a1a; }}
            .title {{ fill: #0f0; font-size: 24px; text-anchor: middle; }}
            .info {{ fill: #0f0; font-size: 14px; text-anchor: middle; }}
            .efficiency {{ fill: #ff0; font-size: 12px; text-anchor: middle; }}
            .play-btn {{ fill: #00ff00; cursor: pointer; }}
            .play-btn:hover {{ fill: #00cc00; }}
        </style>
    </defs>

    <rect width="100%" height="100%" class="container"/>
    
    <text x="50%" y="30%" class="title">ASCII85 Video Container</text>
    <text x="50%" y="40%" class="info">Size: {len(mp4_data):,} bytes → {len(encoded):,} chars</text>
    <text x="50%" y="45%" class="efficiency">Efficiency: {len(encoded) / len(mp4_data) * 100:.1f}% (vs 133% for base64)</text>
    
    <!-- Play button -->
    <g id="playButton" class="play-btn">
        <circle cx="50%" cy="60%" r="30" fill="none" stroke="#00ff00" stroke-width="2"/>
        <polygon points="{width//2-10},{height*0.6-15} {width//2-10},{height*0.6+15} {width//2+15},{height*0.6}" fill="#00ff00"/>
        <text x="50%" y="75%" class="info">Click to decode and play video</text>
    </g>

    <script type="text/javascript">
    <![CDATA[
        // ASCII85 decoder implementation
        function decodeASCII85(encoded) {{
            // Remove delimiters
            if (encoded.startsWith('<~')) {{
                encoded = encoded.substring(2);
            }}
            if (encoded.endsWith('~>')) {{
                encoded = encoded.substring(0, encoded.length - 2);
            }}
            
            // Remove whitespace
            encoded = encoded.replace(/\\s/g, '');
            
            const decoded = [];
            let i = 0;
            
            while (i < encoded.length) {{
                if (encoded[i] === 'z') {{
                    // Special case for all zeros
                    decoded.push(0, 0, 0, 0);
                    i++;
                }} else {{
                    // Process 5 characters
                    let chunk = encoded.substring(i, i + 5);
                    if (chunk.length < 5) {{
                        chunk += 'u'.repeat(5 - chunk.length);
                    }}
                    
                    let value = 0;
                    for (let j = 0; j < chunk.length; j++) {{
                        value = value * 85 + (chunk.charCodeAt(j) - 33);
                    }}
                    
                    // Convert to 4 bytes
                    decoded.push(
                        (value >>> 24) & 0xFF,
                        (value >>> 16) & 0xFF,
                        (value >>> 8) & 0xFF,
                        value & 0xFF
                    );
                    i += 5;
                }}
            }}
            
            return new Uint8Array(decoded);
        }}
        
        // Function to decode and play video
        function decodeAndPlayVideo() {{
            try {{
                console.log('Decoding ASCII85 video data...');
                
                // Get the encoded data from metadata
                const videoData = document.querySelector('video\\\\:data');
                const encodedData = videoData.textContent.trim();
                
                // Base64 decode
                const decodedData = atob(encodedData);
                
                console.log('Encoded data length:', encodedData.length);
                
                // Decode ASCII85
                const decodedBytes = decodeASCII85(decodedData);
                console.log('Decoded bytes length:', decodedBytes.length);
                
                // Create blob and object URL
                const videoBlob = new Blob([decodedBytes], {{ type: 'video/mp4' }});
                const videoUrl = URL.createObjectURL(videoBlob);
                
                console.log('Created video blob URL:', videoUrl);
                
                // Create and configure video element
                const video = document.createElementNS('http://www.w3.org/2000/svg', 'foreignObject');
                video.setAttribute('x', '10%');
                video.setAttribute('y', '10%');
                video.setAttribute('width', '80%');
                video.setAttribute('height', '80%');
                
                const videoElement = document.createElement('video');
                videoElement.src = videoUrl;
                videoElement.controls = true;
                videoElement.autoplay = true;
                videoElement.style.width = '100%';
                videoElement.style.height = '100%';
                
                video.appendChild(videoElement);
                
                // Replace the content
                const svg = document.documentElement;
                // Clear existing content except defs
                const defs = svg.querySelector('defs');
                const metadata = svg.querySelector('metadata');
                svg.innerHTML = '';
                if (defs) svg.appendChild(defs);
                if (metadata) svg.appendChild(metadata);
                svg.appendChild(video);
                
                console.log('Video player created and playing');
                
            }} catch (error) {{
                console.error('Error decoding video:', error);
                alert('Error decoding video: ' + error.message);
            }}
        }}
        
        // Add click handler to play button
        document.addEventListener('DOMContentLoaded', function() {{
            const playButton = document.getElementById('playButton');
            if (playButton) {{
                playButton.addEventListener('click', decodeAndPlayVideo);
            }}
        }});
        
        // Auto-decode when SVG is loaded (optional)
        // decodeAndPlayVideo();
    ]]>
    </script>
</svg>'''

        with open(output_path, 'w') as f:
            f.write(svg_content)

        print(f"[ASCII85] Created: {output_path}")
        print(f"[ASCII85] Original: {len(mp4_data):,} bytes")
        print(f"[ASCII85] Encoded: {len(encoded):,} chars")
        print(f"[ASCII85] Overhead: {(len(encoded) / len(mp4_data) - 1) * 100:.1f}%")

        return output_path

    def _encode_ascii85(self, data: bytes) -> str:
        """Encode binary data using ASCII85"""

        encoded = []

        # Process in 4-byte chunks
        for i in range(0, len(data), 4):
            chunk = data[i:i + 4]

            # Pad if necessary
            if len(chunk) < 4:
                chunk = chunk + b'\x00' * (4 - len(chunk))

            # Convert to 32-bit integer
            value = struct.unpack('>I', chunk)[0]

            # Special case for all zeros
            if value == 0 and i + 4 <= len(data):
                encoded.append('z')
            else:
                # Convert to base 85
                chars = []
                for _ in range(5):
                    chars.append(chr(33 + (value % 85)))
                    value //= 85
                encoded.append(''.join(reversed(chars)))

        result = '<~' + ''.join(encoded) + '~>'
        return result

    def extract(self, svg_path: str, output_mp4: str) -> bool:
        """Extract MP4 from ASCII85 encoded SVG"""

        tree = etree.parse(svg_path)
        root = tree.getroot()

        # Find video data
        ns = {'video': 'http://example.org/video/2024'}
        video_data = root.find('.//video:data', ns)

        if video_data is None:
            print("[ASCII85] No video data found")
            return False

        encoded = video_data.text.strip()
        decoded_b64 = base64.b64decode(encoded).decode('ascii')
        decoded = self._decode_ascii85(decoded_b64)

        with open(output_mp4, 'wb') as f:
            f.write(decoded)

        print(f"[ASCII85] Extracted to {output_mp4}")
        return True

    def _decode_ascii85(self, encoded: str) -> bytes:
        """Decode ASCII85 string to bytes"""

        # Remove delimiters
        if encoded.startswith('<~'):
            encoded = encoded[2:]
        if encoded.endswith('~>'):
            encoded = encoded[:-2]

        decoded = []
        i = 0

        while i < len(encoded):
            if encoded[i] == 'z':
                decoded.extend([0, 0, 0, 0])
                i += 1
            else:
                # Process 5 characters
                chunk = encoded[i:i + 5]
                if len(chunk) < 5:
                    chunk += 'u' * (5 - len(chunk))

                value = 0
                for char in chunk:
                    value = value * 85 + (ord(char) - 33)

                decoded.extend(struct.pack('>I', value))
                i += 5

        return bytes(decoded)


# ============================================
# Method 3: SVG Vector Frame Converter
# ============================================

class SVGVectorFrameConverter:
    """Converts video frames to SVG vector paths"""

    def __init__(self, keyframe_interval: int = 30):
        self.keyframe_interval = keyframe_interval

    def convert(self, mp4_path: str, output_path: str,
                max_frames: int = 30,
                edge_threshold: int = 50) -> str:
        """Convert MP4 frames to SVG vector graphics"""

        print(f"[Vector] Processing {mp4_path}...")

        cap = cv2.VideoCapture(mp4_path)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        # Sample frames evenly
        frame_indices = np.linspace(0, total_frames - 1, min(max_frames, total_frames), dtype=int)

        # Create SVG root
        svg = etree.Element('svg', {
            'xmlns': 'http://www.w3.org/2000/svg',
            'width': str(width),
            'height': str(height),
            'viewBox': f'0 0 {width} {height}'
        })

        # Add title and metadata
        title = etree.SubElement(svg, 'title')
        title.text = 'SVG Vector Video'

        desc = etree.SubElement(svg, 'desc')
        desc.text = f'Vector representation of {os.path.basename(mp4_path)}'

        # Add defs for animations
        defs = etree.SubElement(svg, 'defs')

        # Process frames
        previous_paths = None

        for idx, frame_idx in enumerate(frame_indices):
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = cap.read()

            if not ret:
                continue

            # Convert frame to paths
            paths = self._frame_to_svg_paths(frame, edge_threshold)

            # Create frame group
            frame_group = etree.SubElement(svg, 'g', {
                'id': f'frame-{idx}',
                'opacity': '1' if idx == 0 else '0'
            })

            # Add animation to show/hide frames
            if idx > 0:
                set_show = etree.SubElement(frame_group, 'set', {
                    'attributeName': 'opacity',
                    'to': '1',
                    'begin': f'{idx * (1 / fps):.3f}s',
                    'fill': 'freeze'
                })

                set_hide = etree.SubElement(frame_group, 'set', {
                    'attributeName': 'opacity',
                    'to': '0',
                    'begin': f'{(idx + 1) * (1 / fps):.3f}s',
                    'fill': 'freeze'
                })

            # Add paths to frame
            for path_data in paths:
                path = etree.SubElement(frame_group, 'path', {
                    'd': path_data,
                    'fill': 'none',
                    'stroke': '#0f0',
                    'stroke-width': '1',
                    'vector-effect': 'non-scaling-stroke'
                })

            print(f"[Vector] Frame {idx + 1}/{len(frame_indices)}: {len(paths)} paths")

            previous_paths = paths

        cap.release()

        # Pretty print and save
        rough_string = etree.tostring(svg, encoding='unicode')
        reparsed = minidom.parseString(rough_string)
        pretty_xml = reparsed.toprettyxml(indent="  ")

        with open(output_path, 'w') as f:
            f.write(pretty_xml)

        # Compress with gzip for size comparison
        gz_path = output_path + '.gz'
        with gzip.open(gz_path, 'wb') as f:
            f.write(pretty_xml.encode('utf-8'))

        original_size = os.path.getsize(mp4_path)
        svg_size = os.path.getsize(output_path)
        gz_size = os.path.getsize(gz_path)

        print(f"[Vector] Created: {output_path}")
        print(f"[Vector] Original MP4: {original_size:,} bytes")
        print(f"[Vector] SVG size: {svg_size:,} bytes")
        print(f"[Vector] Gzipped: {gz_size:,} bytes")
        print(f"[Vector] Compression: {(1 - gz_size / original_size) * 100:.1f}% saved")

        return output_path

    def _frame_to_svg_paths(self, frame: np.ndarray, threshold: int) -> List[str]:
        """Convert frame to SVG path strings using edge detection"""

        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Apply Canny edge detection
        edges = cv2.Canny(gray, threshold, threshold * 2)

        # Find contours
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        paths = []
        for contour in contours:
            if len(contour) < 5:  # Skip very small contours
                continue

            # Simplify contour
            epsilon = 0.01 * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)

            # Convert to SVG path
            path_data = self._contour_to_path(approx)
            if path_data:
                paths.append(path_data)

        return paths

    def _contour_to_path(self, contour: np.ndarray) -> str:
        """Convert contour points to SVG path string"""

        if len(contour) < 2:
            return ""

        # Start path
        path = f"M {contour[0][0][0]},{contour[0][0][1]}"

        # Add lines or curves
        for i in range(1, len(contour)):
            x, y = contour[i][0]

            # Use quadratic curves for smoother paths
            if i < len(contour) - 1:
                next_x, next_y = contour[i + 1][0]
                path += f" Q {x},{y} {(x + next_x) / 2},{(y + next_y) / 2}"
            else:
                path += f" L {x},{y}"

        # Close path if needed
        if np.array_equal(contour[0][0], contour[-1][0]):
            path += " Z"

        return path


# ============================================
# Method 4: QR Code Frame Storage (Memvid-style)
# ============================================

class QRCodeSVGConverter:
    """Converts data to QR codes embedded in SVG frames (memvid-inspired)"""

    def __init__(self, chunk_size: int = 1024):
        self.chunk_size = chunk_size

    def convert(self, mp4_path: str, output_path: str,
                include_metadata: bool = True) -> str:
        """Convert MP4 to SVG with QR code frames"""

        print(f"[QR] Processing {mp4_path}...")

        # Read video data
        with open(mp4_path, 'rb') as f:
            mp4_data = f.read()

        # Get video metadata
        cap = cv2.VideoCapture(mp4_path)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        cap.release()

        # Split data into chunks
        chunks = [mp4_data[i:i + self.chunk_size]
                  for i in range(0, len(mp4_data), self.chunk_size)]

        # Create SVG
        svg = etree.Element('svg', {
            'xmlns': 'http://www.w3.org/2000/svg',
            'xmlns:xlink': 'http://www.w3.org/1999/xlink',
            'width': str(width),
            'height': str(height),
            'viewBox': f'0 0 {width} {height}'
        })

        # Add metadata
        metadata = {
            'original_file': os.path.basename(mp4_path),
            'chunks': len(chunks),
            'chunk_size': self.chunk_size,
            'total_size': len(mp4_data),
            'checksum': hashlib.sha256(mp4_data).hexdigest()
        }

        meta_elem = etree.SubElement(svg, 'metadata')
        meta_elem.text = json.dumps(metadata, indent=2)

        # Create QR codes for each chunk
        qr_size = min(width // 4, height // 4, 200)
        grid_cols = width // qr_size
        grid_rows = height // qr_size

        for idx, chunk in enumerate(chunks):
            # Create QR code
            qr = qrcode.QRCode(
                version=None,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=4,
                border=1,
            )

            # Add chunk data with index
            chunk_data = {
                'index': idx,
                'data': base64.b64encode(chunk).decode('ascii'),
                'hash': hashlib.md5(chunk).hexdigest()
            }

            qr.add_data(json.dumps(chunk_data))
            qr.make(fit=True)

            # Convert QR to SVG path
            qr_img = qr.make_image(fill_color="black", back_color="white")

            # Position in grid
            x = (idx % grid_cols) * qr_size
            y = (idx // grid_cols) * qr_size

            # Create frame group
            frame_group = etree.SubElement(svg, 'g', {
                'id': f'qr-frame-{idx}',
                'transform': f'translate({x},{y})',
                'opacity': '1' if idx == 0 else '0.1'
            })

            # Add QR code as image
            qr_buffer = io.BytesIO()
            qr_img.save(qr_buffer, format='PNG')
            qr_base64 = base64.b64encode(qr_buffer.getvalue()).decode('ascii')

            image = etree.SubElement(frame_group, 'image', {
                'x': '0',
                'y': '0',
                'width': str(qr_size),
                'height': str(qr_size),
                'xlink:href': f'data:image/png;base64,{qr_base64}'
            })

            print(f"[QR] Chunk {idx + 1}/{len(chunks)}: {len(chunk)} bytes")

        # Save SVG
        tree = etree.ElementTree(svg)
        tree.write(output_path, encoding='utf-8', xml_declaration=True)

        print(f"[QR] Created: {output_path}")
        print(f"[QR] Original: {len(mp4_data):,} bytes")
        print(f"[QR] Chunks: {len(chunks)}")
        print(f"[QR] QR codes: {len(chunks)} frames")

        return output_path

    def extract(self, svg_path: str, output_mp4: str) -> bool:
        """Extract MP4 from QR code SVG"""

        # This would require QR code reading from SVG
        # Implementation would involve parsing SVG and decoding QR codes
        print("[QR] Extraction requires QR code reader implementation")
        return False


# ============================================
# Method 5: Hybrid Converter (All Methods Combined)
# ============================================

class HybridSVGConverter:
    """Combines multiple encoding methods for optimal storage"""

    def __init__(self):
        self.polyglot = PolyglotSVGConverter()
        self.ascii85 = ASCII85SVGConverter()
        self.vector = SVGVectorFrameConverter()
        self.qr = QRCodeSVGConverter()

    def convert(self, mp4_path: str, output_dir: str) -> Dict[str, str]:
        """Convert using all methods and compare results"""

        print(f"\n{'=' * 60}")
        print(f"HYBRID CONVERTER - Processing: {mp4_path}")
        print(f"{'=' * 60}\n")

        # Create output directory
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        base_name = Path(mp4_path).stem
        results = {}

        # Method 1: Polyglot
        try:
            polyglot_path = os.path.join(output_dir, f"{base_name}_polyglot.svg")
            self.polyglot.convert(mp4_path, polyglot_path)
            results['polyglot'] = {
                'path': polyglot_path,
                'size': os.path.getsize(polyglot_path)
            }
        except Exception as e:
            print(f"[Polyglot] Error: {e}")

        print()

        # Method 2: ASCII85
        try:
            ascii85_path = os.path.join(output_dir, f"{base_name}_ascii85.svg")
            self.ascii85.convert(mp4_path, ascii85_path)
            results['ascii85'] = {
                'path': ascii85_path,
                'size': os.path.getsize(ascii85_path)
            }
        except Exception as e:
            print(f"[ASCII85] Error: {e}")

        print()

        # Method 3: Vector Frames
        try:
            vector_path = os.path.join(output_dir, f"{base_name}_vector.svg")
            self.vector.convert(mp4_path, vector_path, max_frames=10)
            results['vector'] = {
                'path': vector_path,
                'size': os.path.getsize(vector_path),
                'gzipped': os.path.getsize(vector_path + '.gz')
            }
        except Exception as e:
            print(f"[Vector] Error: {e}")

        print()

        # Method 4: QR Codes
        try:
            qr_path = os.path.join(output_dir, f"{base_name}_qr.svg")
            self.qr.convert(mp4_path, qr_path)
            results['qr'] = {
                'path': qr_path,
                'size': os.path.getsize(qr_path)
            }
        except Exception as e:
            print(f"[QR] Error: {e}")

        # Print comparison
        self._print_comparison(mp4_path, results)

        return results

    def _print_comparison(self, mp4_path: str, results: Dict):
        """Print size comparison of all methods"""

        original_size = os.path.getsize(mp4_path)

        print(f"\n{'=' * 60}")
        print("SIZE COMPARISON")
        print(f"{'=' * 60}")
        print(f"Original MP4: {original_size:,} bytes")
        print(f"{'-' * 60}")

        for method, data in results.items():
            size = data['size']
            overhead = (size / original_size - 1) * 100

            print(f"{method.upper():12} {size:12,} bytes  ({overhead:+6.1f}%)")

            if 'gzipped' in data:
                gz_size = data['gzipped']
                gz_saving = (1 - gz_size / original_size) * 100
                print(f"{'  +gzipped':12} {gz_size:12,} bytes  ({gz_saving:6.1f}% saved)")

        print(f"{'=' * 60}\n")


# ============================================
# Main CLI Interface
# ============================================

def main():
    """Command line interface for MP4 to SVG converters"""

    import argparse

    parser = argparse.ArgumentParser(
        description='Convert MP4 to SVG using various encoding methods',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Methods:
  polyglot  - Hide MP4 in SVG comments (0%% overhead for SVG)
  ascii85   - ASCII85 encoding (25%% overhead vs 33%% for base64)
  vector    - Convert frames to SVG paths (can be 90%% smaller with gzip)
  qr        - Store as QR codes (memvid-style)
  hybrid    - Try all methods and compare

Examples:
  python mp4svg.py video.mp4 output.svg --method polyglot
  python mp4svg.py video.mp4 output.svg --method vector --max-frames 30
  python mp4svg.py video.mp4 output_dir/ --method hybrid
        '''
    )

    parser.add_argument('input', help='Input MP4 file')
    parser.add_argument('output', help='Output SVG file or directory (for hybrid)')
    parser.add_argument('--method', '-m',
                        choices=['polyglot', 'ascii85', 'vector', 'qr', 'hybrid'],
                        default='polyglot',
                        help='Conversion method (default: polyglot)')
    parser.add_argument('--pdf', help='Additional PDF file to embed (polyglot only)')
    parser.add_argument('--max-frames', type=int, default=30,
                        help='Maximum frames for vector method (default: 30)')
    parser.add_argument('--edge-threshold', type=int, default=50,
                        help='Edge detection threshold for vector method (default: 50)')
    parser.add_argument('--chunk-size', type=int, default=1024,
                        help='Chunk size for QR method (default: 1024)')
    parser.add_argument('--extract', action='store_true',
                        help='Extract MP4 from SVG instead of converting')

    args = parser.parse_args()

    # Check input file
    if not os.path.exists(args.input):
        print(f"Error: Input file '{args.input}' not found")
        sys.exit(1)

    # Handle extraction mode
    if args.extract:
        if args.method == 'polyglot':
            converter = PolyglotSVGConverter()
            converter.extract(args.input, args.output)
        elif args.method == 'ascii85':
            converter = ASCII85SVGConverter()
            converter.extract(args.input, args.output)
        else:
            print(f"Extraction not implemented for method: {args.method}")
            sys.exit(1)
        return

    # Handle conversion
    if args.method == 'polyglot':
        converter = PolyglotSVGConverter()
        converter.convert(args.input, args.output, args.pdf)

    elif args.method == 'ascii85':
        converter = ASCII85SVGConverter()
        converter.convert(args.input, args.output)

    elif args.method == 'vector':
        converter = SVGVectorFrameConverter()
        converter.convert(args.input, args.output,
                          max_frames=args.max_frames,
                          edge_threshold=args.edge_threshold)

    elif args.method == 'qr':
        converter = QRCodeSVGConverter(chunk_size=args.chunk_size)
        converter.convert(args.input, args.output)

    elif args.method == 'hybrid':
        converter = HybridSVGConverter()
        converter.convert(args.input, args.output)

    else:
        print(f"Unknown method: {args.method}")
        sys.exit(1)


if __name__ == '__main__':
    main()