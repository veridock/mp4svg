#!/usr/bin/env python3
"""
Simple Video to SVG Base64 Data URI Generator with Preview

Generates SVG with <video> element in <foreignObject> using Base64 data URI
from MP4 or WebM video files with first frame preview overlay.

Usage:
    python video2svg.py input.mp4 output.svg
    python video2svg.py input.webm output.svg
"""

import sys
import base64
import os
import argparse
from pathlib import Path
import tempfile


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


def extract_first_frame_thumbnail(video_path: str, scale: float = 0.2) -> str:
    """
    Extract first frame from video and return as Base64 data URI thumbnail.
    
    Args:
        video_path: Path to video file
        scale: Scale factor for thumbnail (default 0.2 = 20%)
    
    Returns:
        Base64 data URI string for the thumbnail
    """
    try:
        import cv2
        from PIL import Image
        
        print(f"🖼️ Extracting first frame thumbnail at {scale*100:.0f}% scale...")
        
        # Open video and get first frame
        cap = cv2.VideoCapture(video_path)
        ret, frame = cap.read()
        cap.release()
        
        if not ret:
            print("⚠️ Could not extract first frame")
            return ""
        
        # Convert BGR to RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Convert to PIL Image
        pil_image = Image.fromarray(frame_rgb)
        
        # Calculate thumbnail size
        original_width, original_height = pil_image.size
        thumb_width = int(original_width * scale)
        thumb_height = int(original_height * scale)
        
        # Create thumbnail
        pil_image.thumbnail((thumb_width, thumb_height), Image.Resampling.LANCZOS)
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
            pil_image.save(temp_file.name, 'PNG', optimize=True)
            temp_path = temp_file.name
        
        # Read back and encode as Base64
        with open(temp_path, 'rb') as f:
            thumbnail_data = f.read()
        
        # Clean up temp file
        os.unlink(temp_path)
        
        # Create data URI
        thumbnail_b64 = base64.b64encode(thumbnail_data).decode('ascii')
        data_uri = f"data:image/png;base64,{thumbnail_b64}"
        
        print(f"✅ Thumbnail created: {thumb_width}x{thumb_height} ({len(thumbnail_data):,} bytes)")
        
        return data_uri
        
    except ImportError:
        print("⚠️ opencv-python and/or Pillow not available - skipping thumbnail")
        return ""
    except Exception as e:
        print(f"⚠️ Error creating thumbnail: {e}")
        return ""


def generate_video_svg(video_path: str, output_path: str) -> None:
    """
    Generate SVG with Base64 data URI video in foreignObject with preview thumbnail.
    
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
    
    # Extract first frame thumbnail
    thumbnail_data_uri = extract_first_frame_thumbnail(video_path, scale=0.2)
    
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
    
    # Generate thumbnail overlay (if available)
    thumbnail_overlay = ""
    if thumbnail_data_uri:
        # Calculate thumbnail position (centered)
        thumb_x = width // 2
        thumb_y = height // 2
        
        thumbnail_overlay = f'''
  <!-- Preview thumbnail overlay (visible before video plays) -->
  <image href="{thumbnail_data_uri}" 
         x="0" y="0" 
         id="preview-thumbnail" 
         opacity="1.0"
         style="pointer-events: none; width: 100%; height: 100%;">
    <title>Video Preview</title>
  </image>
  
  <!-- Play button overlay -->
  <g id="play-button" opacity="0.8" style="cursor: pointer;">
    <circle cx="{thumb_x}" cy="{thumb_y}" r="30" fill="rgba(0,0,0,0.6)" stroke="white" stroke-width="2"/>
    <polygon points="{thumb_x-8},{thumb_y-12} {thumb_x-8},{thumb_y+12} {thumb_x+12},{thumb_y}" fill="white"/>
  </g>'''
    
    # Generate JavaScript for interactive behavior
    interactive_js = '''
    <script type="text/javascript">
    <![CDATA[
    (function() {
        // Wait for DOM to be ready
        function onReady() {
            const video = document.querySelector('video');
            const thumbnail = document.getElementById('preview-thumbnail');
            const playButton = document.getElementById('play-button');
            
            if (!video) return;
            
            // Hide preview when video starts playing
            function hidePreview() {
                if (thumbnail) thumbnail.style.opacity = '0';
                if (playButton) playButton.style.opacity = '0';
            }
            
            // Show preview when video ends/pauses
            function showPreview() {
                if (thumbnail) thumbnail.style.opacity = '1';
                if (playButton) playButton.style.opacity = '0.8';
            }
            
            // Event listeners
            video.addEventListener('play', hidePreview);
            video.addEventListener('playing', hidePreview);
            video.addEventListener('pause', showPreview);
            video.addEventListener('ended', showPreview);
            
            // Click handler for play button
            if (playButton) {
                playButton.addEventListener('click', function() {
                    video.play().catch(function(e) {
                        console.log('Video play failed:', e);
                    });
                });
            }
            
            // Click handler for thumbnail
            if (thumbnail) {
                thumbnail.addEventListener('click', function() {
                    video.play().catch(function(e) {
                        console.log('Video play failed:', e);
                    });
                });
            }
            
            console.log('Video SVG with preview ready');
        }
        
        // Initialize when ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', onReady);
        } else {
            onReady();
        }
    })();
    ]]>
    </script>'''
    
    # Generate SVG with embedded video and preview
    svg_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
  <title>Base64 Video SVG with Preview</title>
  <desc>Video embedded as Base64 data URI in SVG foreignObject with first frame preview</desc>
  {thumbnail_overlay}
  
  <foreignObject width="{width}" height="{height}">
    <body xmlns="http://www.w3.org/1999/xhtml" style="margin: 0; padding: 0;">
      <video autoplay="false" loop="true" muted="true" width="{width}" height="{height}" style="display: block;">
        <source src="{data_uri}" type="{mime_type}" />
        <p>Your browser does not support HTML5 video.</p>
      </video>
    </body>
  </foreignObject>
  
  {interactive_js}
  
  <!-- Metadata -->
  <metadata>
    <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
             xmlns:dc="http://purl.org/dc/elements/1.1/">
      <rdf:Description rdf:about="">
        <dc:title>Base64 Video SVG with Preview</dc:title>
        <dc:description>Video file embedded as Base64 data URI with first frame preview</dc:description>
        <dc:creator>video2svg.py</dc:creator>
        <dc:source>{os.path.basename(video_path)}</dc:source>
        <dc:format>image/svg+xml</dc:format>
        <dc:type>Interactive Video with Preview</dc:type>
      </rdf:Description>
    </rdf:RDF>
  </metadata>
</svg>'''
    
    # Write SVG file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(svg_content)
    
    # Get output file size
    output_size = os.path.getsize(output_path)
    
    print(f"🎯 SVG with preview generated successfully!")
    print(f"   Output: {output_path}")
    print(f"   SVG size: {output_size:,} bytes")
    if thumbnail_data_uri:
        print(f"   ✅ First frame preview included (20% scale)")
        print(f"   🎮 Click thumbnail or play button to start video")
    print(f"   Ready to open in browser!")


def main():
    """Command line interface."""
    parser = argparse.ArgumentParser(
        description='Generate SVG with Base64 data URI video from MP4/WebM files with first frame preview',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python video2svg.py video.mp4 output.svg
  python video2svg.py animation.webm result.svg
  
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
