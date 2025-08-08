#!/usr/bin/env python3
"""
Video to SVG Base64 Data URI Generator with Audio Support

Generates SVG with <video> element in <foreignObject> using Base64 data URI
from MP4 or WebM video files with audio playback and controls.

Usage:
    python video2svg.py input.mp4 output.svg
    python video2svg.py input.webm output.svg --with-controls
    python video2svg.py input.mp4 output.svg --autoplay --unmuted
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
    mime_types = {
        '.mp4': 'video/mp4',
        '.webm': 'video/webm',
        '.ogg': 'video/ogg',
        '.ogv': 'video/ogg',
        '.avi': 'video/x-msvideo',
        '.mov': 'video/quicktime',
        '.mkv': 'video/x-matroska',
        '.m4v': 'video/mp4'
    }
    return mime_types.get(ext, 'video/mp4')


def get_video_info(file_path: str) -> dict:
    """
    Get video dimensions and audio info using ffprobe or opencv.
    """
    info = {
        'width': 640,
        'height': 360,
        'has_audio': False,
        'duration': 0
    }

    # Try ffprobe first (more reliable for audio detection)
    try:
        import subprocess
        import json

        cmd = [
            'ffprobe', '-v', 'error',
            '-show_streams',
            '-select_streams', 'v:0',
            '-of', 'json',
            file_path
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            data = json.loads(result.stdout)
            if data.get('streams'):
                stream = data['streams'][0]
                info['width'] = int(stream.get('width', 640))
                info['height'] = int(stream.get('height', 360))

        # Check for audio stream
        cmd_audio = [
            'ffprobe', '-v', 'error',
            '-select_streams', 'a:0',
            '-show_entries', 'stream=codec_type',
            '-of', 'json',
            file_path
        ]

        result_audio = subprocess.run(cmd_audio, capture_output=True, text=True)
        if result_audio.returncode == 0:
            data_audio = json.loads(result_audio.stdout)
            info['has_audio'] = bool(data_audio.get('streams'))

    except Exception:
        pass

    # Fallback to opencv
    if info['width'] == 640:  # Default value, try opencv
        try:
            import cv2
            cap = cv2.VideoCapture(file_path)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            cap.release()
            if width > 0 and height > 0:
                info['width'] = width
                info['height'] = height
        except Exception:
            pass

    return info


def extract_first_frame_thumbnail(video_path: str, scale: float = 0.3) -> str:
    """
    Extract first frame from video and return as Base64 data URI thumbnail.

    Args:
        video_path: Path to video file
        scale: Scale factor for thumbnail (default 0.3 = 30%)

    Returns:
        Base64 data URI string for the thumbnail
    """
    try:
        import cv2
        from PIL import Image

        print(f"🖼️  Extracting first frame thumbnail at {scale * 100:.0f}% scale...")

        # Open video and get first frame
        cap = cv2.VideoCapture(video_path)
        ret, frame = cap.read()
        cap.release()

        if not ret:
            print("⚠️  Could not extract first frame")
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

        # Save to temporary file with high compression
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
            pil_image.save(temp_file.name, 'JPEG', quality=60, optimize=True)
            temp_path = temp_file.name

        # Read back and encode as Base64
        with open(temp_path, 'rb') as f:
            thumbnail_data = f.read()

        # Clean up temp file
        os.unlink(temp_path)

        # Create data URI
        thumbnail_b64 = base64.b64encode(thumbnail_data).decode('ascii')
        data_uri = f"data:image/jpeg;base64,{thumbnail_b64}"

        print(f"✅ Thumbnail created: {thumb_width}x{thumb_height} ({len(thumbnail_data):,} bytes)")

        return data_uri

    except ImportError:
        print("⚠️  opencv-python and/or Pillow not available - skipping thumbnail")
        return ""
    except Exception as e:
        print(f"⚠️  Error creating thumbnail: {e}")
        return ""


def generate_video_svg(video_path: str, output_path: str,
                       autoplay: bool = False,
                       muted: bool = True,
                       controls: bool = True,
                       loop: bool = True,
                       thumbnail_scale: float = 0.3) -> None:
    """
    Generate SVG with Base64 data URI video in foreignObject with audio support.

    Args:
        video_path: Path to input video file (MP4/WebM)
        output_path: Path to output SVG file
        autoplay: Whether to autoplay the video
        muted: Whether to mute the video initially
        controls: Whether to show video controls
        loop: Whether to loop the video
        thumbnail_scale: Scale factor for thumbnail preview
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
    info = get_video_info(video_path)
    width = info['width']
    height = info['height']
    has_audio = info['has_audio']

    print(f"📊 Video info:")
    print(f"   Size: {file_size:,} bytes")
    print(f"   MIME: {mime_type}")
    print(f"   Dimensions: {width}x{height}")
    print(f"   Audio: {'Yes 🔊' if has_audio else 'No 🔇'}")

    # Extract first frame thumbnail (only if not autoplay)
    thumbnail_data_uri = ""
    if not autoplay:
        thumbnail_data_uri = extract_first_frame_thumbnail(video_path, scale=thumbnail_scale)

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

    # Video attributes
    video_attrs = []
    if autoplay:
        video_attrs.append('autoplay="true"')
    if muted:
        video_attrs.append('muted="true"')
    if controls:
        video_attrs.append('controls="true"')
    if loop:
        video_attrs.append('loop="true"')

    video_attrs_str = ' '.join(video_attrs)

    # Generate thumbnail overlay (only if not autoplay and thumbnail available)
    thumbnail_overlay = ""
    if thumbnail_data_uri and not autoplay:
        # Calculate play button position (centered)
        play_x = width // 2
        play_y = height // 2

        thumbnail_overlay = f'''
  <!-- Preview thumbnail overlay (visible before video plays) -->
  <image href="{thumbnail_data_uri}" 
         x="0" y="0" 
         width="{width}" height="{height}"
         id="preview-thumbnail" 
         opacity="1.0"
         style="cursor: pointer;">
    <title>Click to play video{' with audio' if has_audio else ''}</title>
  </image>

  <!-- Play button overlay -->
  <g id="play-button" opacity="0.9" style="cursor: pointer;">
    <circle cx="{play_x}" cy="{play_y}" r="40" fill="rgba(0,0,0,0.7)" stroke="white" stroke-width="3"/>
    <polygon points="{play_x - 12},{play_y - 18} {play_x - 12},{play_y + 18} {play_x + 16},{play_y}" fill="white"/>
  </g>'''

        # Add audio indicator if video has audio
        if has_audio:
            thumbnail_overlay += f'''

  <!-- Audio indicator -->
  <g id="audio-indicator" opacity="0.8">
    <rect x="10" y="10" width="120" height="30" rx="15" fill="rgba(0,0,0,0.6)" stroke="white" stroke-width="1"/>
    <text x="70" y="30" text-anchor="middle" fill="white" font-family="Arial" font-size="14">🔊 With Audio</text>
  </g>'''

    # Generate JavaScript for interactive behavior with audio support
    interactive_js = '''
    <script type="text/javascript">
    <![CDATA[
    (function() {
        // Wait for DOM to be ready
        function onReady() {
            const video = document.querySelector('video');
            const thumbnail = document.getElementById('preview-thumbnail');
            const playButton = document.getElementById('play-button');
            const audioIndicator = document.getElementById('audio-indicator');

            if (!video) return;

            // Hide preview when video starts playing
            function hidePreview() {
                if (thumbnail) {
                    thumbnail.style.opacity = '0';
                    thumbnail.style.pointerEvents = 'none';
                }
                if (playButton) {
                    playButton.style.opacity = '0';
                    playButton.style.pointerEvents = 'none';
                }
                if (audioIndicator) {
                    audioIndicator.style.opacity = '0';
                }
            }

            // Show preview when video ends/pauses
            function showPreview() {
                if (!video.seeking && !video.currentTime) {
                    if (thumbnail) {
                        thumbnail.style.opacity = '1';
                        thumbnail.style.pointerEvents = 'auto';
                    }
                    if (playButton) {
                        playButton.style.opacity = '0.9';
                        playButton.style.pointerEvents = 'auto';
                    }
                    if (audioIndicator) {
                        audioIndicator.style.opacity = '0.8';
                    }
                }
            }

            // Play video with audio
            function playVideo() {
                // Unmute for audio playback
                video.muted = false;
                video.play().then(function() {
                    console.log('Video playing with audio');
                }).catch(function(e) {
                    // If autoplay with audio fails, try muted
                    console.log('Autoplay with audio failed, trying muted:', e);
                    video.muted = true;
                    video.play().catch(function(e2) {
                        console.log('Video play failed:', e2);
                    });
                });
            }

            // Event listeners
            video.addEventListener('play', hidePreview);
            video.addEventListener('playing', hidePreview);
            video.addEventListener('pause', function() {
                if (video.currentTime === 0) {
                    showPreview();
                }
            });
            video.addEventListener('ended', function() {
                video.currentTime = 0;
                showPreview();
            });

            // Click handlers for play button and thumbnail
            if (playButton) {
                playButton.addEventListener('click', playVideo);
            }

            if (thumbnail) {
                thumbnail.addEventListener('click', playVideo);
            }

            // Volume control hint
            video.addEventListener('volumechange', function() {
                console.log('Volume:', video.volume, 'Muted:', video.muted);
            });

            // Enable audio on first user interaction (for browsers that block autoplay)
            function enableAudioOnInteraction() {
                video.muted = false;
                document.removeEventListener('click', enableAudioOnInteraction);
                document.removeEventListener('touchstart', enableAudioOnInteraction);
            }

            if (video.muted && video.autoplay) {
                document.addEventListener('click', enableAudioOnInteraction);
                document.addEventListener('touchstart', enableAudioOnInteraction);
            }

            console.log('Video SVG ready - Audio:', video.muted ? 'Muted' : 'Enabled');
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

    # Generate SVG with embedded video with audio support
    svg_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="{width}" height="{height}" 
     xmlns="http://www.w3.org/2000/svg" 
     xmlns:xlink="http://www.w3.org/1999/xlink"
     viewBox="0 0 {width} {height}">

  <title>Video with Audio Support</title>
  <desc>Video embedded as Base64 data URI with audio playback support</desc>

  {thumbnail_overlay if not autoplay else ''}

  <foreignObject width="{width}" height="{height}">
    <body xmlns="http://www.w3.org/1999/xhtml" style="margin: 0; padding: 0; background: #000;">
      <video {video_attrs_str} 
             width="{width}" 
             height="{height}" 
             style="display: block; width: 100%; height: 100%; object-fit: contain;"
             preload="metadata">
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
        <dc:title>Video with Audio</dc:title>
        <dc:description>Video file embedded as Base64 data URI with audio support</dc:description>
        <dc:creator>video2svg.py</dc:creator>
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

    print(f"\n🎯 SVG generated successfully!")
    print(f"   Output: {output_path}")
    print(f"   SVG size: {output_size:,} bytes")

    # Print usage instructions
    print(f"\n📖 Usage instructions:")
    if controls:
        print(f"   ✅ Video controls enabled - use player controls")
    if has_audio:
        print(f"   🔊 Audio {'enabled' if not muted else 'muted initially'}")
        if not autoplay:
            print(f"   🎵 Click play button to start with audio")
        elif muted:
            print(f"   🎵 Click anywhere on video to unmute")
    if thumbnail_data_uri and not autoplay:
        print(f"   👆 Click thumbnail or play button to start")
    if autoplay:
        print(f"   ▶️  Video will autoplay {'(muted)' if muted else ''}")
    print(f"\n   Ready to open in browser!")


def main():
    """Command line interface."""
    parser = argparse.ArgumentParser(
        description='Generate SVG with Base64 video and audio support',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Basic conversion with controls and audio
  python video2svg.py video.mp4 output.svg

  # Autoplay with audio (will be muted initially in most browsers)
  python video2svg.py video.mp4 output.svg --autoplay --unmuted

  # No controls, autoplay muted with loop
  python video2svg.py animation.webm loop.svg --autoplay --no-controls

  # With all features
  python video2svg.py video.mp4 output.svg --with-controls --unmuted

Audio Notes:
  • Most browsers block autoplay with audio (security feature)
  • Use --unmuted to enable audio (requires user interaction)
  • Click play button or video to start audio playback
  • Controls enabled by default for user convenience
        '''
    )

    parser.add_argument('input', help='Input video file (MP4, WebM, etc.)')
    parser.add_argument('output', help='Output SVG file')

    # Video control options
    parser.add_argument('--autoplay', action='store_true',
                        help='Enable autoplay (usually muted by browsers)')
    parser.add_argument('--no-loop', action='store_true',
                        help='Disable video loop')
    parser.add_argument('--no-controls', action='store_true',
                        help='Hide video controls')
    parser.add_argument('--with-controls', action='store_true',
                        help='Force show controls (default)')

    # Audio options
    parser.add_argument('--unmuted', action='store_true',
                        help='Start unmuted (enable audio)')
    parser.add_argument('--muted', action='store_true',
                        help='Start muted (default for autoplay)')

    # Thumbnail options
    parser.add_argument('--thumbnail-scale', type=float, default=0.3,
                        help='Thumbnail scale factor (0.1-1.0, default: 0.3)')
    parser.add_argument('--no-thumbnail', action='store_true',
                        help='Skip thumbnail generation')

    # Dimension overrides
    parser.add_argument('--width', type=int, help='Override video width')
    parser.add_argument('--height', type=int, help='Override video height')

    args = parser.parse_args()

    try:
        # Override dimensions if provided
        if args.width and args.height:
            global get_video_info
            original_func = get_video_info

            def custom_info(path):
                info = original_func(path)
                info['width'] = args.width
                info['height'] = args.height
                return info

            get_video_info = custom_info

        # Determine muted state
        muted = not args.unmuted  # Default is muted unless --unmuted is specified
        if args.autoplay and not args.unmuted:
            muted = True  # Force muted for autoplay unless explicitly unmuted

        # Determine controls state
        controls = not args.no_controls  # Default is to show controls

        # Generate SVG
        generate_video_svg(
            args.input,
            args.output,
            autoplay=args.autoplay,
            muted=muted,
            controls=controls,
            loop=not args.no_loop,
            thumbnail_scale=args.thumbnail_scale if not args.no_thumbnail else 0
        )

    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()