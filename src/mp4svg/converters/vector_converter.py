"""
Vector SVG converter for MP4 to SVG
Converts video frames to SVG vector paths using edge detection
"""

import os
import cv2
import numpy as np
from lxml import etree
from xml.dom import minidom
from ..base import BaseConverter, EncodingError


class SVGVectorFrameConverter(BaseConverter):
    """Converts video frames to SVG vector graphics"""

    def __init__(self, keyframe_interval: int = 30):
        self.keyframe_interval = keyframe_interval

    def convert(self, mp4_path: str, output_path: str, 
                max_frames: int = 30, edge_threshold: int = 50) -> str:
        """Convert MP4 frames to SVG vector graphics"""
        
        self._validate_input(mp4_path)
        print(f"[Vector] Processing {mp4_path}...")
        print(f"[Vector] Max frames: {max_frames}, Edge threshold: {edge_threshold}")

        try:
            cap = cv2.VideoCapture(mp4_path)
            metadata = self._get_video_metadata(mp4_path)
            
            width = metadata['width']
            height = metadata['height'] 
            fps = metadata['fps']
            total_frames = metadata['frame_count']

            # Calculate frame indices to extract
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
            for idx, frame_num in enumerate(frame_indices):
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
                ret, frame = cap.read()
                if not ret:
                    continue

                print(f"[Vector] Processing frame {idx + 1}/{len(frame_indices)}")

                # Convert frame to SVG paths
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
                        'dur': f'{1 / fps:.3f}s'
                    })

                    set_hide = etree.SubElement(frame_group, 'set', {
                        'attributeName': 'opacity',
                        'to': '0',
                        'begin': f'{(idx + 1) * (1 / fps):.3f}s',
                        'dur': f'{1 / fps:.3f}s'
                    })

                # Add paths to frame
                for path_data in paths:
                    path = etree.SubElement(frame_group, 'path', {
                        'd': path_data,
                        'fill': 'none',
                        'stroke': '#0f0',
                        'stroke-width': '1',
                        'opacity': '0.8'
                    })

                previous_paths = paths

            cap.release()

            # Pretty print and save
            rough_string = etree.tostring(svg, encoding='unicode')
            reparsed = minidom.parseString(rough_string)
            pretty_xml = reparsed.toprettyxml(indent="  ")

            # Remove extra whitespace
            lines = [line for line in pretty_xml.split('\n') if line.strip()]
            final_xml = '\n'.join(lines)

            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(final_xml)

            file_size = os.path.getsize(output_path)
            print(f"[Vector] Created: {output_path}")
            print(f"[Vector] Frames processed: {len(frame_indices)}")
            print(f"[Vector] SVG size: {file_size:,} bytes")
            print(f"[Vector] Note: Use gzip compression for ~90% size reduction")

            return output_path
            
        except Exception as e:
            raise EncodingError(f"Vector conversion failed: {str(e)}")

    def extract(self, svg_path: str, output_mp4: str) -> bool:
        """Vector SVG cannot be directly converted back to MP4"""
        print("[Vector] Warning: Vector SVG cannot be converted back to original MP4")
        print("[Vector] Vector representation is lossy - original video data is not preserved")
        return False

    def _frame_to_svg_paths(self, frame: np.ndarray, threshold: int) -> list:
        """Convert frame to SVG path strings using edge detection"""
        
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Apply Gaussian blur
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Edge detection
        edges = cv2.Canny(blurred, threshold, threshold * 2)
        
        # Find contours
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        paths = []
        for contour in contours:
            # Filter small contours
            if cv2.contourArea(contour) < 50:
                continue
            
            # Simplify contour
            epsilon = 0.02 * cv2.arcLength(contour, True)
            simplified = cv2.approxPolyDP(contour, epsilon, True)
            
            # Convert to SVG path
            path_data = self._contour_to_path(simplified)
            if path_data:
                paths.append(path_data)
        
        return paths

    def _contour_to_path(self, contour: np.ndarray) -> str:
        """Convert contour points to SVG path string"""
        
        if len(contour) < 3:
            return ""
        
        path_parts = []
        
        # Start with move to first point
        first_point = contour[0][0]
        path_parts.append(f"M {first_point[0]},{first_point[1]}")
        
        # Add line segments
        for point in contour[1:]:
            x, y = point[0]
            path_parts.append(f"L {x},{y}")
        
        # Close path
        path_parts.append("Z")
        
        return " ".join(path_parts)
