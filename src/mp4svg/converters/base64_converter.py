"""
Base64 SVG Converter - Embeds MP4 video as Base64 data in SVG with HTML5 video player fallback.

This converter encodes the MP4 video data as Base64 and embeds it directly in the SVG
with JavaScript for decoding and playback using HTML5 video element.
"""

import base64
import struct
from typing import Optional
from ..base import BaseConverter


class Base64SVGConverter(BaseConverter):
    """
    Base64 SVG Converter.
    
    Embeds MP4 video as Base64 encoded data in SVG with:
    - Base64 thumbnail preview for system compatibility
    - JavaScript decoder for browser video playback
    - IndexedDB fallback for robust in-SVG video player
    - Multiple fallback layers for maximum compatibility
    """
    
    def __init__(self):
        super().__init__()
        self.method_name = "base64"
    
    def convert(self, video_path: str, output_path: str, 
                width: Optional[int] = None, height: Optional[int] = None) -> str:
        """
        Convert MP4 video to SVG with Base64 encoding.
        
        Args:
            video_path: Path to input MP4 file
            output_path: Path to output SVG file
            width: Optional width for SVG canvas
            height: Optional height for SVG canvas
            
        Returns:
            Path to created SVG file
        """
        print(f"[BASE64] Processing {video_path}...")
        
        # Read video data
        with open(video_path, 'rb') as f:
            video_data = f.read()
        
        # Get video dimensions
        if not width or not height:
            metadata = self._get_video_metadata(video_path)
            width, height = metadata['width'], metadata['height']
        
        # Generate Base64 encoded video
        base64_encoded = self._encode_base64(video_data)
        
        # Create thumbnail for preview
        thumbnail_base64, thumb_width, thumb_height = self._create_thumbnail(video_path)
        
        # Generate SVG with embedded Base64 video
        svg_content = self._generate_svg(
            base64_encoded, thumbnail_base64, width, height
        )
        
        # Write SVG file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(svg_content)
        
        print(f"[BASE64] Created: {output_path}")
        print(f"[BASE64] Original: {len(video_data):,} bytes")
        print(f"[BASE64] Encoded: {len(base64_encoded):,} chars")
        print(f"[BASE64] Overhead: {((len(base64_encoded) - len(video_data)) / len(video_data)) * 100:.1f}%")
        print(f"[BASE64] Added thumbnail: {len(thumbnail_base64)} chars")
        
        return output_path
    
    def extract(self, svg_path: str, output_path: str) -> bool:
        """
        Extract MP4 video from Base64 SVG file.
        
        Args:
            svg_path: Path to input SVG file
            output_path: Path to output MP4 file
            
        Returns:
            True if extraction successful, False otherwise
        """
        try:
            print(f"[BASE64] Extracting from {svg_path}...")
            
            # Read SVG file
            with open(svg_path, 'r', encoding='utf-8') as f:
                svg_content = f.read()
            
            # Find Base64 data
            start_marker = '<text id="base64VideoData"'
            end_marker = '</text>'
            
            start_idx = svg_content.find(start_marker)
            if start_idx == -1:
                print("[BASE64] Base64 video data not found in SVG")
                return False
            
            # Find the actual Base64 content between tags
            content_start = svg_content.find('>', start_idx) + 1
            content_end = svg_content.find(end_marker, content_start)
            
            if content_end == -1:
                print("[BASE64] End of Base64 data not found")
                return False
            
            # Extract and clean Base64 data
            base64_data = svg_content[content_start:content_end].strip()
            
            if not base64_data:
                print("[BASE64] No Base64 data found")
                return False
            
            print(f"[BASE64] Found Base64 data: {len(base64_data)} chars")
            
            # Decode Base64 to binary data
            video_data = self._decode_base64(base64_data)
            print(f"[BASE64] Decoded to: {len(video_data)} bytes")
            
            # Write MP4 file
            with open(output_path, 'wb') as f:
                f.write(video_data)
            
            print(f"[BASE64] Extracted: {output_path}")
            print(f"[BASE64] Video size: {len(video_data):,} bytes")
            
            return True
            
        except Exception as e:
            print(f"[BASE64] Extraction error: {e}")
            return False
    
    def _encode_base64(self, data: bytes) -> str:
        """Encode binary data to Base64 string."""
        return base64.b64encode(data).decode('ascii')
    
    def _decode_base64(self, encoded: str) -> bytes:
        """Decode Base64 string to bytes."""
        return base64.b64decode(encoded.encode('ascii'))
    
    def _generate_svg(self, base64_data: str, thumbnail_base64: str, width: int, height: int) -> str:
        """Generate SVG content with embedded Base64 video and JavaScript decoder."""
        
        js_decoder = f'''
        <script type="text/javascript"><![CDATA[
            // Base64 Video Decoder and Player for mp4svg
            console.log('Base64 mp4svg player initialized');
            
            function decodeBase64(base64Str) {{
                console.log('Decoding Base64 video data...');
                try {{
                    // Decode Base64 to binary string
                    const binaryString = atob(base64Str);
                    console.log(`Decoded Base64: ${{base64Str.length}} chars -> ${{binaryString.length}} bytes`);
                    
                    // Convert to Uint8Array
                    const bytes = new Uint8Array(binaryString.length);
                    for (let i = 0; i < binaryString.length; i++) {{
                        bytes[i] = binaryString.charCodeAt(i);
                    }}
                    
                    return bytes;
                }} catch (error) {{
                    console.error('Base64 decode error:', error);
                    return null;
                }}
            }}
            
            function decodeAndPlayVideo() {{
                try {{
                    // Find the Base64 video data
                    const videoDataNode = document.querySelector('#base64VideoData');
                    if (!videoDataNode) {{
                        console.error('Base64 video data not found');
                        return;
                    }}
                    
                    const base64Data = videoDataNode.textContent.trim();
                    if (!base64Data) {{
                        console.error('Base64 video data is empty');
                        return;
                    }}
                    
                    console.log('Creating video container...');
                    
                    // Decode Base64 to video data
                    const videoBytes = decodeBase64(base64Data);
                    if (!videoBytes) {{
                        console.error('Failed to decode Base64 video data');
                        return;
                    }}
                    
                    // Create Blob and URL
                    const videoBlob = new Blob([videoBytes], {{ type: 'video/mp4' }});
                    const videoUrl = URL.createObjectURL(videoBlob);
                    
                    console.log('Video Blob created:', videoBlob.size, 'bytes');
                    
                    // Try IndexedDB fallback for in-SVG playback
                    tryIndexedDBPlayback(videoBytes, videoUrl);
                    
                }} catch (error) {{
                    console.error('Error decoding video:', error);
                    // Final fallback - trigger download
                    console.log('Triggering video download as final fallback...');
                    triggerVideoDownload();
                }}
            }}
            
            function tryIndexedDBPlayback(videoBytes, videoUrl) {{
                console.log('Attempting IndexedDB in-SVG playback...');
                try {{
                    // Store video in IndexedDB and create in-SVG player
                    const request = indexedDB.open('mp4svgVideos', 1);
                    
                    request.onsuccess = function(event) {{
                        const db = event.target.result;
                        const transaction = db.transaction(['videos'], 'readwrite');
                        const store = transaction.objectStore('videos');
                        
                        const videoId = 'current_video_' + Date.now();
                        store.put({{ id: videoId, data: videoBytes }});
                        
                        transaction.oncomplete = function() {{
                            console.log('Video stored in IndexedDB, creating in-SVG player...');
                            createInSVGVideoPlayer(videoUrl);
                        }};
                    }};
                    
                    request.onupgradeneeded = function(event) {{
                        const db = event.target.result;
                        if (!db.objectStoreNames.contains('videos')) {{
                            db.createObjectStore('videos', {{ keyPath: 'id' }});
                        }}
                    }};
                    
                    request.onerror = function() {{
                        console.error('IndexedDB failed, trying popup fallback...');
                        tryPopupPlayback(videoUrl);
                    }};
                    
                }} catch (error) {{
                    console.error('IndexedDB setup failed:', error);
                    tryPopupPlayback(videoUrl);
                }}
            }}
            
            function createInSVGVideoPlayer(videoUrl) {{
                console.log('Creating in-SVG video player...');
                try {{
                    // Create foreignObject element for in-SVG video player
                    const foreignObject = document.createElementNS('http://www.w3.org/2000/svg', 'foreignObject');
                    foreignObject.setAttribute('x', '0');
                    foreignObject.setAttribute('y', '0'); 
                    foreignObject.setAttribute('width', '100%');
                    foreignObject.setAttribute('height', '100%');
                    foreignObject.setAttribute('style', 'position: absolute; top: 0; left: 0; z-index: 10000;');
                    
                    // Build HTML video player content programmatically (avoid innerHTML XML parsing issues)
                    const overlay = document.createElement('div');
                    if (overlay.style && overlay.style.cssText !== undefined) {{
                        overlay.style.cssText = 'position: absolute; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.9); z-index: 10000;';
                    }} else {{
                        overlay.setAttribute('style', 'position: absolute; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.9); z-index: 10000;');
                    }}
                    
                    const centered = document.createElement('div');
                    if (centered.style && centered.style.cssText !== undefined) {{
                        centered.style.cssText = 'position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 90%; max-width: 800px;';
                    }} else {{
                        centered.setAttribute('style', 'position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 90%; max-width: 800px;');
                    }}
                    
                    const panel = document.createElement('div');
                    if (panel.style && panel.style.cssText !== undefined) {{
                        panel.style.cssText = 'background: #000; padding: 20px; border-radius: 10px; box-shadow: 0 4px 20px rgba(0,0,0,0.5);';
                    }} else {{
                        panel.setAttribute('style', 'background: #000; padding: 20px; border-radius: 10px; box-shadow: 0 4px 20px rgba(0,0,0,0.5);');
                    }}
                    
                    const title = document.createElement('div');
                    if (title.style && title.style.cssText !== undefined) {{
                        title.style.cssText = 'color: white; margin-bottom: 10px; font-family: Arial, sans-serif; font-size: 16px;';
                    }} else {{
                        title.setAttribute('style', 'color: white; margin-bottom: 10px; font-family: Arial, sans-serif; font-size: 16px;');
                    }}
                    title.textContent = '📼 Mp4svg Base64 Player';
                    
                    const video = document.createElement('video');
                    video.setAttribute('controls', 'true');
                    video.setAttribute('autoplay', 'true');
                    if (video.style && video.style.cssText !== undefined) {{
                        video.style.cssText = 'width: 100%; height: auto; border-radius: 5px;';
                    }} else {{
                        video.setAttribute('style', 'width: 100%; height: auto; border-radius: 5px;');
                    }}
                    video.src = videoUrl;
                    
                    const buttonDiv = document.createElement('div');
                    if (buttonDiv.style && buttonDiv.style.cssText !== undefined) {{
                        buttonDiv.style.cssText = 'margin-top: 10px; text-align: right;';
                    }} else {{
                        buttonDiv.setAttribute('style', 'margin-top: 10px; text-align: right;');
                    }}
                    
                    const closeButton = document.createElement('button');
                    if (closeButton.style && closeButton.style.cssText !== undefined) {{
                        closeButton.style.cssText = 'background: #f44336; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer; font-family: Arial, sans-serif;';
                    }} else {{
                        closeButton.setAttribute('style', 'background: #f44336; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer; font-family: Arial, sans-serif;');
                    }}
                    closeButton.textContent = '✕ Close';
                    closeButton.onclick = () => foreignObject.remove();
                    
                    const info = document.createElement('div');
                    if (info.style && info.style.cssText !== undefined) {{
                        info.style.cssText = 'color: #888; margin-top: 5px; font-family: Arial, sans-serif; font-size: 12px;';
                    }} else {{
                        info.setAttribute('style', 'color: #888; margin-top: 5px; font-family: Arial, sans-serif; font-size: 12px;');
                    }}
                    info.textContent = 'Video loaded from IndexedDB • Base64 decoded • Embedded in SVG foreignObject';
                    
                    // Build DOM structure
                    buttonDiv.appendChild(closeButton);
                    panel.appendChild(title);
                    panel.appendChild(video);
                    panel.appendChild(buttonDiv);
                    panel.appendChild(info);
                    centered.appendChild(panel);
                    overlay.appendChild(centered);
                    foreignObject.appendChild(overlay);
                    
                    // Add foreignObject to the SVG
                    const svgElement = document.querySelector('svg');
                    if (svgElement) {{
                        svgElement.appendChild(foreignObject);
                        console.log('In-SVG video player created successfully!');
                    }} else {{
                        console.error('SVG element not found for in-SVG player');
                        tryPopupPlayback(videoUrl);
                    }}
                    
                }} catch (error) {{
                    console.error('Failed to create in-SVG player:', error);
                    tryPopupPlayback(videoUrl);
                }}
            }}
            
            function tryPopupPlayback(videoUrl) {{
                console.log('Trying popup video playback...');
                try {{
                    const popup = window.open('', '_blank', 'width=800,height=600');
                    if (popup) {{
                        popup.document.write(`
                            <html><head><title>Mp4svg Base64 Video</title></head>
                            <body style="margin:0;padding:20px;background:#000;">
                                <video controls autoplay style="width:100%;height:auto;">
                                    <source src="${{videoUrl}}" type="video/mp4">
                                </video>
                                <p style="color:white;">Mp4svg Base64 decoded video</p>
                            </body></html>
                        `);
                        console.log('Video opened in popup window');
                    }} else {{
                        console.log('Popup blocked, trying new tab...');
                        tryNewTabPlayback(videoUrl);
                    }}
                }} catch (error) {{
                    console.error('Popup failed:', error);
                    tryNewTabPlayback(videoUrl);
                }}
            }}
            
            function tryNewTabPlayback(videoUrl) {{
                console.log('Trying new tab video playback...');
                try {{
                    const newTab = window.open(videoUrl, '_blank');
                    if (newTab) {{
                        console.log('Video opened in new tab');
                    }} else {{
                        console.log('New tab blocked, triggering download...');
                        triggerVideoDownload();
                    }}
                }} catch (error) {{
                    console.error('New tab failed:', error);
                    triggerVideoDownload();
                }}
            }}
            
            function triggerVideoDownload() {{
                console.log('Triggering video download...');
                try {{
                    const videoDataNode = document.querySelector('#base64VideoData');
                    if (videoDataNode) {{
                        const base64Data = videoDataNode.textContent.trim();
                        const videoBytes = decodeBase64(base64Data);
                        if (videoBytes) {{
                            const blob = new Blob([videoBytes], {{ type: 'video/mp4' }});
                            const url = URL.createObjectURL(blob);
                            const a = document.createElement('a');
                            a.href = url;
                            a.download = 'mp4svg_base64_video.mp4';
                            document.body.appendChild(a);
                            a.click();
                            document.body.removeChild(a);
                            URL.revokeObjectURL(url);
                            console.log('Video download triggered');
                        }}
                    }}
                }} catch (error) {{
                    console.error('Download failed:', error);
                }}
            }}
            
            // Auto-setup when DOM loads
            document.addEventListener('DOMContentLoaded', function() {{
                console.log('Base64 mp4svg DOM loaded, setting up play button...');
                
                // Add click handler to play button
                const playButton = document.querySelector('.play-button');
                if (playButton) {{
                    playButton.addEventListener('click', function(e) {{
                        e.preventDefault();
                        console.log('Play button clicked, starting Base64 decode...');
                        decodeAndPlayVideo();
                    }});
                    
                    // Add hover effect
                    playButton.addEventListener('mouseenter', function() {{
                        this.style.opacity = '0.8';
                    }});
                    playButton.addEventListener('mouseleave', function() {{
                        this.style.opacity = '1.0';
                    }});
                    
                    console.log('Base64 play button setup complete');
                }} else {{
                    console.error('Play button not found');
                }}
            }});
        ]]></script>
        '''
        
        svg_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
    <defs>
        <style>
            .play-button {{
                cursor: pointer;
                transition: all 0.3s ease;
            }}
            .play-button:hover {{
                opacity: 0.8;
            }}
            .overlay {{
                fill: rgba(0, 0, 0, 0.3);
            }}
            .play-icon {{
                fill: white;
                stroke: white;
                stroke-width: 2;
            }}
        </style>
    </defs>
    
    <!-- Background thumbnail -->
    <image x="0" y="0" width="{width}" height="{height}" href="data:image/jpeg;base64,{thumbnail_base64}" />
    
    <!-- Play button overlay -->
    <g class="play-button">
        <rect x="0" y="0" width="{width}" height="{height}" class="overlay" />
        <circle cx="{width//2}" cy="{height//2}" r="50" fill="rgba(255, 255, 255, 0.9)" stroke="rgba(0, 0, 0, 0.3)" stroke-width="3"/>
        <polygon points="{width//2-20},{height//2-25} {width//2-20},{height//2+25} {width//2+25},{height//2}" class="play-icon"/>
    </g>
    
    <!-- Embedded Base64 video data (hidden) -->
    <text id="base64VideoData" style="display: none;">{base64_data}</text>
    
    {js_decoder}
    
    <!-- Metadata -->
    <metadata>
        <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
                 xmlns:dc="http://purl.org/dc/elements/1.1/">
            <rdf:Description rdf:about="">
                <dc:title>Mp4svg Base64 Video</dc:title>
                <dc:description>MP4 video embedded in SVG using Base64 encoding</dc:description>
                <dc:creator>mp4svg Base64 converter</dc:creator>
                <dc:format>image/svg+xml</dc:format>
                <dc:type>Interactive Video</dc:type>
            </rdf:Description>
        </rdf:RDF>
    </metadata>
</svg>'''
        
        return svg_content
