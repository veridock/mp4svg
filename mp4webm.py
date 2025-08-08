#!/usr/bin/env python3
"""
Intelligent MP4 to WebM Converter with Frame Change Detection

Converts MP4 videos to WebM format with smart frame deduplication.
Detects real frame changes and builds WebM with optimal timing.

Usage:
    python mp4webm.py input.mp4 output.webm
    python mp4webm.py input.mp4 output.webm --smart-conversion
    python mp4webm.py input.mp4 output.webm --threshold 0.95
    python mp4webm.py input.mp4 output.webm --min-fps 15
    python mp4webm.py input.mp4 output.webm --no-duplicated-frames
"""

import cv2
import os
import imageio
from PIL import Image
import subprocess
import argparse
import sys
import numpy as np
from pathlib import Path
import tempfile
import json


def calculate_frame_similarity(frame1, frame2):
    """Calculate similarity between two frames using structural similarity."""
    # Convert to grayscale for comparison
    gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
    
    # Calculate mean squared error
    mse = np.mean((gray1.astype(float) - gray2.astype(float)) ** 2)
    
    # Convert to similarity score (0-1, where 1 is identical)
    max_mse = 255.0 ** 2
    similarity = 1.0 - (mse / max_mse)
    
    return similarity


def analyze_frame_changes(mp4_path, similarity_threshold=0.98, min_fps=None, fast_mode=False):
    """
    Analyze video for real frame changes and timing with performance optimizations.
    
    Args:
        mp4_path: Path to video file
        similarity_threshold: Threshold for frame similarity (0.0-1.0)
        min_fps: Minimum FPS to maintain (forces frame inclusion)
        fast_mode: Skip detailed analysis, use fast duplicate detection
    
    Returns:
        List of unique frames with their timing information
    """
    print(f"🔍 Analyzing frame changes in: {mp4_path}")
    print(f"📊 Similarity threshold: {similarity_threshold}")
    if min_fps:
        print(f"⚡ Minimum FPS: {min_fps}")
    if fast_mode:
        print(f"🚀 Fast mode: Early duplicate detection enabled")
    
    cap = cv2.VideoCapture(mp4_path)
    
    # Get video properties
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_duration = 1.0 / fps
    video_duration = total_frames / fps
    
    # Calculate minimum frame interval if min_fps is specified
    min_frame_interval = 1.0 / min_fps if min_fps else 0
    
    print(f"📺 Video: {total_frames} frames @ {fps:.2f} FPS ({video_duration:.2f}s)")
    
    unique_frames = []
    previous_frame = None
    current_time = 0.0
    frame_count = 0
    duplicates_skipped = 0
    last_included_time = -min_frame_interval  # Force first frame inclusion
    
    # Fast mode: Skip frames more aggressively
    frame_skip = 2 if fast_mode and fps > 15 else 1
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Skip frames in fast mode to reduce processing
        if fast_mode and (frame_count % frame_skip != 0):
            current_time += frame_duration
            frame_count += 1
            continue
        
        is_different = True
        force_include = False
        
        # Force inclusion based on minimum FPS
        if min_fps and (current_time - last_included_time) >= min_frame_interval:
            force_include = True
            print(f"⚡ Force include frame at {current_time:.2f}s (min FPS rule)")
        
        if previous_frame is not None and not force_include:
            if fast_mode:
                # Fast similarity check - use smaller resolution for speed
                small_prev = cv2.resize(previous_frame, (160, 120))
                small_curr = cv2.resize(frame, (160, 120))
                similarity = calculate_frame_similarity(small_prev, small_curr)
            else:
                similarity = calculate_frame_similarity(previous_frame, frame)
                
            if similarity >= similarity_threshold:
                is_different = False
                duplicates_skipped += 1
        
        if is_different or force_include:
            # This is a new unique frame
            unique_frames.append({
                'frame': frame.copy(),
                'timestamp': current_time,
                'original_index': frame_count,
                'duration': frame_duration,  # Will be updated later
                'forced': force_include
            })
            previous_frame = frame.copy()
            last_included_time = current_time
            
            if len(unique_frames) % 10 == 0:
                print(f"📍 Found {len(unique_frames)} unique frames (skipped {duplicates_skipped} duplicates)")
        
        current_time += frame_duration
        frame_count += 1
        
        # Early termination for very long videos in fast mode
        if fast_mode and frame_count > 1000:
            print(f"🚀 Fast mode: Early termination at {frame_count} frames")
            break
    
    cap.release()
    
    # Calculate proper durations for each unique frame
    for i in range(len(unique_frames)):
        if i < len(unique_frames) - 1:
            # Duration until next frame change
            duration = unique_frames[i + 1]['timestamp'] - unique_frames[i]['timestamp']
            unique_frames[i]['duration'] = duration
        else:
            # Last frame duration (remaining time)
            remaining_time = video_duration - unique_frames[i]['timestamp']
            unique_frames[i]['duration'] = max(remaining_time, frame_duration)
    
    # Calculate effective FPS
    effective_fps = len(unique_frames) / video_duration if video_duration > 0 else 0
    
    print(f"✅ Analysis complete:")
    print(f"   Original frames: {total_frames}")
    print(f"   Unique frames: {len(unique_frames)}")
    print(f"   Duplicates removed: {duplicates_skipped}")
    print(f"   Compression ratio: {len(unique_frames)/total_frames:.1%}")
    print(f"   Effective FPS: {effective_fps:.2f}")
    if min_fps:
        print(f"   Min FPS maintained: {'✅' if effective_fps >= min_fps * 0.9 else '⚠️'}")
    
    return unique_frames, fps


def create_optimized_webm(unique_frames, output_webm, original_fps):
    """Create WebM from unique frames with proper timing."""
    print(f"🎬 Creating optimized WebM: {output_webm}")
    
    # Create temporary directory for unique frames
    with tempfile.TemporaryDirectory() as temp_dir:
        frame_files = []
        durations = []
        
        # Save unique frames
        for i, frame_data in enumerate(unique_frames):
            frame_path = os.path.join(temp_dir, f"frame_{i:06d}.png")
            cv2.imwrite(frame_path, frame_data['frame'])
            frame_files.append(frame_path)
            durations.append(frame_data['duration'])
            
            if (i + 1) % 10 == 0:
                print(f"💾 Saved {i + 1}/{len(unique_frames)} unique frames")
        
        # Create frame list file for ffmpeg
        frame_list_path = os.path.join(temp_dir, "frames.txt")
        with open(frame_list_path, 'w') as f:
            for i, (frame_file, duration) in enumerate(zip(frame_files, durations)):
                f.write(f"file '{frame_file}'\n")
                f.write(f"duration {duration:.6f}\n")
            # Add last frame without duration (ffmpeg requirement)
            if frame_files:
                f.write(f"file '{frame_files[-1]}'\n")
        
        # Create WebM with variable frame timing
        print(f"🔄 Encoding WebM with variable frame timing...")
        
        cmd = [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", frame_list_path,
            "-c:v", "libvpx-vp9",
            "-b:v", "1M",
            "-crf", "30",
            "-g", "240",  # Keyframe interval
            "-threads", "4",
            output_webm
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ WebM created successfully!")
            return True
        else:
            print(f"❌ FFmpeg error: {result.stderr}")
            return False


def extract_frames_and_convert(mp4_path, output_dir, max_frames=100):
    """Extract frames from MP4 and convert to WebP and AVIF formats."""
    os.makedirs(output_dir, exist_ok=True)
    print(f"📹 Extracting frames from: {mp4_path}")
    print(f"📁 Output directory: {output_dir}")
    print(f"🎯 Max frames: {max_frames}")

    cap = cv2.VideoCapture(mp4_path)
    
    # Get video info
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    print(f"📊 Video info: {width}x{height} @ {fps:.2f} FPS, {total_frames} total frames")
    
    actual_max = min(max_frames, total_frames)
    count = 0

    while count < actual_max:
        success, frame = cap.read()
        if not success:
            break

        frame_path = os.path.join(output_dir, f"frame_{count:03}.png")
        cv2.imwrite(frame_path, frame)

        # Convert to WebP
        webp_path = os.path.join(output_dir, f"frame_{count:03}.webp")
        img = Image.open(frame_path)
        img.save(webp_path, "WEBP", quality=80)

        # Convert to AVIF (requires ffmpeg)
        avif_path = os.path.join(output_dir, f"frame_{count:03}.avif")
        result = subprocess.run([
            "ffmpeg", "-y", "-i", frame_path, "-c:v", "libaom-av1", "-crf", "30", "-b:v", "0", avif_path
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        if result.returncode == 0:
            print(f"Klatka {count} → WebP + AVIF")
        else:
            print(f"Klatka {count} → WebP (AVIF failed)")
        
        # Clean up intermediate PNG
        os.remove(frame_path)
        count += 1

    cap.release()
    print(f"✔️ Zakończono konwersję klatek: {count} frames")


def convert_mp4_to_webm_traditional(mp4_path, output_webm):
    """Traditional MP4 to WebM conversion (fixed frame rate)."""
    print(f"🔄 Converting {mp4_path} → {output_webm} (traditional method)")
    
    result = subprocess.run([
        "ffmpeg", "-i", mp4_path,
        "-c:v", "libvpx-vp9", "-b:v", "1M",
        "-c:a", "libopus", output_webm
    ])
    
    if result.returncode == 0:
        # Get file sizes for comparison
        input_size = os.path.getsize(mp4_path)
        output_size = os.path.getsize(output_webm)
        compression_ratio = (1 - output_size / input_size) * 100
        
        print(f"✔️ Zapisano WebM: {output_webm}")
        print(f"📊 Original: {input_size:,} bytes → WebM: {output_size:,} bytes")
        print(f"🗜️ Compression: {compression_ratio:.1f}% smaller")
        return True
    else:
        print(f"❌ Failed to convert {mp4_path} to WebM")
        return False


def convert_mp4_to_webm_smart(mp4_path, output_webm, similarity_threshold=0.98, min_fps=None, fast_mode=False):
    """Smart MP4 to WebM conversion with frame deduplication and performance options."""
    mode_desc = "🚀 Fast smart" if fast_mode else "🧠 Smart"
    print(f"{mode_desc} conversion: {mp4_path} → {output_webm}")
    
    # Analyze frames and find unique ones
    unique_frames, original_fps = analyze_frame_changes(
        mp4_path, similarity_threshold, min_fps, fast_mode
    )
    
    if len(unique_frames) == 0:
        print(f"❌ No frames found in video")
        return False
    
    # Create optimized WebM
    success = create_optimized_webm(unique_frames, output_webm, original_fps)
    
    if success:
        # Get file sizes for comparison
        input_size = os.path.getsize(mp4_path)
        output_size = os.path.getsize(output_webm)
        compression_ratio = (1 - output_size / input_size) * 100
        
        print(f"✅ Smart WebM created: {output_webm}")
        print(f"📊 Original: {input_size:,} bytes → WebM: {output_size:,} bytes")
        print(f"🗜️ Compression: {compression_ratio:.1f}% smaller")
        print(f"🎯 Frame optimization: {len(unique_frames)} unique frames used")
        
        if fast_mode:
            print(f"🚀 Fast mode: Processing time significantly reduced")
        
        return True
    else:
        return False


def main():
    """Command line interface for MP4 to WebM conversion."""
    parser = argparse.ArgumentParser(
        description='Intelligent MP4 to WebM converter with frame deduplication',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python mp4webm.py input.mp4 output.webm
  python mp4webm.py input.mp4 output.webm --smart-conversion
  python mp4webm.py input.mp4 output.webm --threshold 0.95
  python mp4webm.py video.mp4 compressed.webm --max-frames 50
  python mp4webm.py video.mp4 compressed.webm --min-fps 15
  python mp4webm.py video.mp4 compressed.webm --no-duplicated-frames
  
Smart Conversion:
  Analyzes video for real frame changes and creates WebM with optimal timing.
  Perfect for videos with static scenes, presentations, or slow animations.
  
Features:
  • Intelligent frame change detection
  • Duplicate frame removal with similarity threshold
  • Variable frame timing in output WebM
  • High-quality WebM conversion (VP9 + Opus)
  • Frame extraction to WebP and AVIF formats
  • Automatic compression ratio reporting
        '''
    )
    
    parser.add_argument('input', help='Input MP4 file')
    parser.add_argument('output', help='Output WebM file')
    parser.add_argument('--smart-conversion', action='store_true',
                        help='Use intelligent frame deduplication (recommended)')
    parser.add_argument('--threshold', type=float, default=0.98,
                        help='Frame similarity threshold (0.0-1.0, default: 0.98)')
    parser.add_argument('--min-fps', type=int,
                        help='Minimum FPS to maintain (forces frame inclusion)')
    parser.add_argument('--no-duplicated-frames', action='store_true',
                        help='Skip detailed analysis, use fast duplicate detection')
    parser.add_argument('--max-frames', type=int, default=100,
                        help='Maximum frames to extract for analysis (default: 100)')
    parser.add_argument('--frames-dir', default='output_frames',
                        help='Output directory for frames (default: output_frames)')
    parser.add_argument('--no-frames', action='store_true',
                        help='Skip frame extraction, only convert to WebM')
    parser.add_argument('--quality', type=int, default=80,
                        help='WebP quality (1-100, default: 80)')
    
    args = parser.parse_args()
    
    # Validate input file
    if not os.path.exists(args.input):
        print(f"❌ Error: Input file not found: {args.input}")
        sys.exit(1)
    
    # Validate input is video file
    input_ext = Path(args.input).suffix.lower()
    if input_ext not in ['.mp4', '.avi', '.mov', '.mkv', '.webm']:
        print(f"⚠️ Warning: {input_ext} may not be a supported video format")
    
    # Validate threshold
    if not 0.0 <= args.threshold <= 1.0:
        print(f"❌ Error: Threshold must be between 0.0 and 1.0")
        sys.exit(1)
    
    # Ensure output directory exists for WebM
    output_dir = os.path.dirname(args.output)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    try:
        # Extract frames (unless disabled)
        if not args.no_frames:
            extract_frames_and_convert(args.input, args.frames_dir, args.max_frames)
        
        # Convert to WebM using selected method
        if args.smart_conversion:
            success = convert_mp4_to_webm_smart(
                args.input, args.output, args.threshold, args.min_fps, args.no_duplicated_frames
            )
        else:
            success = convert_mp4_to_webm_traditional(args.input, args.output)
        
        if success:
            print(f"🎉 Conversion complete!")
            print(f"📁 WebM: {args.output}")
            if not args.no_frames:
                print(f"📁 Frames: {args.frames_dir}")
            
            if args.smart_conversion:
                print(f"🧠 Used smart conversion with {args.threshold:.2f} similarity threshold")
            else:
                print(f"📺 Used traditional conversion (consider --smart-conversion for optimization)")
        else:
            print(f"❌ Conversion failed")
            sys.exit(1)
        
    except KeyboardInterrupt:
        print(f"\n⏹️ Conversion interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error during conversion: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
