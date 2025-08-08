#!/usr/bin/env python3
"""
Simple Video to SVG Base64 Data URI Generator

Generates SVG with <video> element in <foreignObject> using Base64 data URI
from MP4 or WebM video files. Clean and lightweight approach.

Usage:
    python video_to_svg.py input.mp4 output.svg
    python video_to_svg.py input.webm output.svg
"""

import sys
import base64
import os
import argparse
from pathlib import Path


def get_video_mime_type(file_path: str) -> str:
    """Get MIME type based on file extension."""
    ext = Path(file_path).suffix.lower()
    if ext == '.mp4':
        return 'video/mp4'
    elif ext == '.webm':
        return 'video/webm'
    elif ext == '.ogg':
        return 'video/ogg'
    elif ext == '.avi':
        return 'video/avi'
    elif ext == '.mov':
        return 'video/quicktime'
    else:
        return 'video/mp4'  # Default fallback


def get_video_dimensions(file_path: str) -> tuple:
    """
    Try to get video dimensions using opencv if available.
    Otherwise return default dimensions.
    """
    try:
        import cv2
        cap = cv2.VideoCapture(file_path)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        cap.release()
        if width > 0 and height > 0:
            return width, height
    except ImportError:
        print("Note: opencv-python not available, using default dimensions")
    except Exception:
        print("Note: Could not read video dimensions, using default")
    
    # Default dimensions
    return 640, 360


def generate_video_svg(video_path: str, output_path: str) -> None:
    """
    Generate SVG with Base64 data URI video in foreignObject.
    
    Args:
        video_path: Path to input video file (MP4/WebM)
        output_path: Path to output SVG file
    """
    # Validate input file
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")
    
    print(f"📹 Processing: {video_path}")
    
    # Read video data
    with open(video_path, 'rb') as f:
        video_data = f.read()
    
    # Get video info
    file_size = len(video_data)
    mime_type = get_video_mime_type(video_path)
    width, height = get_video_dimensions(video_path)
    
    print(f"📊 Video info:")
    print(f"   Size: {file_size:,} bytes")
    print(f"   MIME: {mime_type}")
    print(f"   Dimensions: {width}x{height}")
    
    # Encode to Base64
    print(f"🔄 Encoding to Base64...")
    base64_data = base64.b64encode(video_data).decode('ascii')
    data_uri = f"data:{mime_type};base64,{base64_data}"
    
    # Calculate overhead
    encoded_size = len(base64_data)
    overhead = ((encoded_size - file_size) / file_size) * 100
    
    print(f"✅ Base64 encoding complete:")
    print(f"   Original: {file_size:,} bytes")
    print(f"   Encoded: {encoded_size:,} chars")
    print(f"   Overhead: {overhead:.1f}%")
    
    # Generate SVG with embedded video
    svg_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">
  <title>Base64 Video SVG</title>
  <desc>Video embedded as Base64 data URI in SVG foreignObject</desc>
  
  <foreignObject width="{width}" height="{height}">
    <body xmlns="http://www.w3.org/1999/xhtml" style="margin: 0; padding: 0;">
      <video autoplay="true" loop="true" muted="true" width="{width}" height="{height}" style="display: block;">
        <source src="{data_uri}" type="{mime_type}" />
        <p>Your browser does not support HTML5 video.</p>
      </video>
    </body>
  </foreignObject>
  
  <!-- Metadata -->
  <metadata>
    <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
             xmlns:dc="http://purl.org/dc/elements/1.1/">
      <rdf:Description rdf:about="">
        <dc:title>Base64 Video SVG</dc:title>
        <dc:description>Video file embedded as Base64 data URI</dc:description>
        <dc:creator>video_to_svg.py</dc:creator>
        <dc:source>{os.path.basename(video_path)}</dc:source>
        <dc:format>image/svg+xml</dc:format>
        <dc:type>Interactive Video</dc:type>
      </rdf:Description>
    </rdf:RDF>
  </metadata>
</svg>'''
    
    # Write SVG file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(svg_content)
    
    # Get output file size
    output_size = os.path.getsize(output_path)
    
    print(f"🎯 SVG generated successfully!")
    print(f"   Output: {output_path}")
    print(f"   SVG size: {output_size:,} bytes")
    print(f"   Ready to open in browser!")


def main():
    """Command line interface."""
    parser = argparse.ArgumentParser(
        description='Generate SVG with Base64 data URI video from MP4/WebM files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python video_to_svg.py video.mp4 output.svg
  python video_to_svg.py animation.webm result.svg
  
Features:
  • Simple Base64 data URI embedding
  • Video in <foreignObject> for clean SVG structure  
  • Autoplay, loop, muted for web compatibility
  • Automatic MIME type detection
  • Dimension detection (if opencv available)
  • No external dependencies required
        '''
    )
    
    parser.add_argument('input', help='Input video file (MP4, WebM, etc.)')
    parser.add_argument('output', help='Output SVG file')
    parser.add_argument('--width', type=int, help='Override video width')
    parser.add_argument('--height', type=int, help='Override video height')
    parser.add_argument('--no-autoplay', action='store_true', help='Disable autoplay')
    parser.add_argument('--no-loop', action='store_true', help='Disable loop')
    parser.add_argument('--no-muted', action='store_true', help='Disable muted')
    
    args = parser.parse_args()
    
    try:
        # Override dimensions if provided
        if args.width and args.height:
            # Monkey patch get_video_dimensions for this run
            global get_video_dimensions
            original_func = get_video_dimensions
            get_video_dimensions = lambda _: (args.width, args.height)
        
        generate_video_svg(args.input, args.output)
        
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
