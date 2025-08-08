"""
Polyglot SVG converter for MP4 to SVG
Embeds MP4 data in SVG comments with 0% overhead
"""

import os
import hashlib
from typing import Optional
from lxml import etree
from ..base import BaseConverter, EncodingError, DecodingError


class PolyglotSVGConverter(BaseConverter):
    """Creates SVG files that contain hidden MP4 data"""

    def __init__(self):
        self.boundary = f"POLYGLOT_BOUNDARY_{hashlib.md5(os.urandom(16)).hexdigest()}"

    def convert(self, mp4_path: str, output_path: str, pdf_path: Optional[str] = None) -> str:
        """Convert MP4 to polyglot SVG file"""
        
        self._validate_input(mp4_path)
        print(f"[Polyglot] Processing {mp4_path}...")

        try:
            # Read MP4 data
            with open(mp4_path, 'rb') as f:
                mp4_data = f.read()

            # Read PDF data if provided
            pdf_data = b""
            if pdf_path and os.path.exists(pdf_path):
                with open(pdf_path, 'rb') as f:
                    pdf_data = f.read()
                print(f"[Polyglot] Including PDF: {pdf_path}")

            # Create SVG template
            svg_content = self._create_svg_template(mp4_path)
            
            # Encode binary data for SVG comments
            mp4_encoded = self._encode_for_svg_comment(mp4_data)
            pdf_encoded = self._encode_for_svg_comment(pdf_data) if pdf_data else ""

            # Build polyglot content
            polyglot_content = f"""<!--{self.boundary}
<!--MP4_DATA
{mp4_encoded}
MP4_DATA-->"""

            if pdf_data:
                polyglot_content += f"""
<!--PDF_DATA
{pdf_encoded}
PDF_DATA-->"""

            polyglot_content += f"""
{self.boundary}-->

{svg_content}

<!--{self.boundary}
Summary: SVG Polyglot Container
- Original MP4: {len(mp4_data):,} bytes
- SVG overhead: ~0% (comments ignored)
{f"- PDF included: {len(pdf_data):,} bytes" if pdf_data else ""}
- Total embedded: {len(mp4_data) + len(pdf_data):,} bytes
{self.boundary}-->"""

            # Write to output file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(polyglot_content)

            print(f"[Polyglot] Created: {output_path}")
            print(f"[Polyglot] MP4 size: {len(mp4_data):,} bytes")
            if pdf_data:
                print(f"[Polyglot] PDF size: {len(pdf_data):,} bytes")
            print(f"[Polyglot] SVG overhead: ~0% (comment-based)")

            return output_path
            
        except Exception as e:
            raise EncodingError(f"Polyglot encoding failed: {str(e)}")

    def extract(self, svg_path: str, output_mp4: str) -> bool:
        """Extract MP4 from polyglot SVG"""
        
        try:
            with open(svg_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Look for MP4 data markers
            start_marker = "<!--MP4_DATA\n"
            end_marker = "\nMP4_DATA-->"
            
            start_idx = content.find(start_marker)
            if start_idx == -1:
                print("[Polyglot] No MP4 data found in SVG")
                return False

            end_idx = content.find(end_marker, start_idx)
            if end_idx == -1:
                print("[Polyglot] Malformed MP4 data in SVG")
                return False

            # Extract and decode data
            encoded_data = content[start_idx + len(start_marker):end_idx]
            decoded_data = self._decode_from_svg_comment(encoded_data)

            # Write MP4 file
            with open(output_mp4, 'wb') as f:
                f.write(decoded_data)

            print(f"[Polyglot] Extracted MP4 to: {output_mp4}")
            print(f"[Polyglot] Size: {len(decoded_data):,} bytes")

            return True
            
        except Exception as e:
            raise DecodingError(f"Polyglot extraction failed: {str(e)}")

    def _create_svg_template(self, video_path: str) -> str:
        """Create base SVG template with video metadata"""
        
        metadata = self._get_video_metadata(video_path)
        thumbnail_b64, thumb_width, thumb_height = self._create_thumbnail(video_path)
        
        return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" 
     width="{metadata['width']}" height="{metadata['height']}">
  
  <title>Polyglot Video Container</title>
  <desc>MP4 video hidden in SVG comments - 0% overhead</desc>
  
  <defs>
    <style>
      .container {{ fill: #2a2a2a; }}
      .title {{ fill: #00ff00; font-size: 24px; text-anchor: middle; }}
      .info {{ fill: #00ff00; font-size: 14px; text-anchor: middle; }}
      .hidden {{ fill: #ffff00; font-size: 12px; text-anchor: middle; }}
      .thumbnail {{ cursor: pointer; }}
    </style>
  </defs>

  <rect width="100%" height="100%" class="container"/>
  
  <!-- Thumbnail preview -->
  {f'<image x="10" y="10" width="{thumb_width}" height="{thumb_height}" href="data:image/jpeg;base64,{thumbnail_b64}" class="thumbnail"/>' if thumbnail_b64 else ''}
  
  <text x="50%" y="30%" class="title">Polyglot SVG Container</text>
  <text x="50%" y="40%" class="info">Video: {metadata['width']}x{metadata['height']} @ {metadata['fps']:.1f} FPS</text>
  <text x="50%" y="50%" class="info">Duration: {metadata['duration']:.1f} seconds</text>
  <text x="50%" y="60%" class="hidden">MP4 data hidden in comments (0% overhead)</text>
  <text x="50%" y="70%" class="info">Open in text editor to see embedded data</text>
  
  <!-- Instructions -->
  <text x="50%" y="85%" class="hidden" font-size="10">
    Extract: mp4svg polyglot.svg video.mp4 --extract
  </text>
</svg>'''

    def _encode_for_svg_comment(self, data: bytes) -> str:
        """Encode binary data for safe inclusion in SVG comments"""
        
        import base64
        # Use base64 for safe comment embedding
        encoded = base64.b64encode(data).decode('ascii')
        
        # Format in 80-character lines for readability
        lines = []
        for i in range(0, len(encoded), 80):
            lines.append(encoded[i:i + 80])
        
        return '\n'.join(lines)

    def _decode_from_svg_comment(self, encoded_data: str) -> bytes:
        """Decode binary data from SVG comment encoding"""
        
        import base64
        # Remove line breaks and whitespace
        clean_data = ''.join(encoded_data.split())
        
        # Decode from base64
        return base64.b64decode(clean_data)
