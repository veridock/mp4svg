#!/usr/bin/env python3
"""
Ultra-Fast MP4 to WebM Converter

Optimized for maximum speed conversion using hardware acceleration when available.
"""

import subprocess
import os
import sys
import argparse
from pathlib import Path
import time


def get_video_info(input_path):
    """Get basic video information using ffprobe."""
    cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height,r_frame_rate,duration,nb_frames",
        "-of", "json", input_path
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        import json
        data = json.loads(result.stdout)
        if data.get('streams'):
            return data['streams'][0]
    except:
        pass
    return None


def convert_ultrafast(input_path, output_path, preset="ultrafast", crf=35):
    """
    Ultra-fast conversion using FFmpeg with speed optimizations.

    Args:
        input_path: Input video file
        output_path: Output WebM file
        preset: Speed preset (ultrafast, superfast, veryfast, faster, fast)
        crf: Quality (0-63, lower is better, 35 is fast/decent balance)
    """
    print(f"🚀 ULTRA-FAST conversion mode")
    print(f"📥 Input: {input_path}")
    print(f"📤 Output: {output_path}")
    print(f"⚡ Preset: {preset}, CRF: {crf}")

    start_time = time.time()

    # Get input file size
    input_size = os.path.getsize(input_path)

    # FFmpeg command optimized for speed
    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        # Video codec settings
        "-c:v", "libvpx-vp9",
        "-deadline", "realtime",  # Fastest encoding
        "-cpu-used", "8",  # Maximum speed (0-8, 8 is fastest)
        "-crf", str(crf),
        "-b:v", "0",  # Let CRF control quality
        "-row-mt", "1",  # Enable row-based multithreading
        "-threads", "0",  # Use all available threads
        # Audio settings (if present)
        "-c:a", "libopus",
        "-b:a", "128k",
        # Output
        output_path
    ]

    print("⏳ Converting...")
    result = subprocess.run(cmd, capture_output=True, text=True)

    elapsed = time.time() - start_time

    if result.returncode == 0:
        output_size = os.path.getsize(output_path)
        compression_ratio = (1 - output_size / input_size) * 100

        print(f"✅ SUCCESS! Conversion completed in {elapsed:.1f} seconds")
        print(f"📊 Original: {input_size:,} bytes → WebM: {output_size:,} bytes")
        print(f"🗜️ Compression: {compression_ratio:.1f}% smaller")
        print(f"⚡ Speed: {input_size / elapsed / 1024 / 1024:.1f} MB/s")
        return True
    else:
        print(f"❌ Error: {result.stderr}")
        return False


def convert_hardware_accelerated(input_path, output_path, gpu="auto"):
    """
    Hardware-accelerated conversion (requires compatible GPU).

    Args:
        input_path: Input video file
        output_path: Output WebM file
        gpu: GPU type (auto, nvidia, intel, amd)
    """
    print(f"🎮 Hardware-accelerated conversion")
    print(f"📥 Input: {input_path}")
    print(f"📤 Output: {output_path}")

    start_time = time.time()
    input_size = os.path.getsize(input_path)

    # Try NVIDIA NVENC first (fastest if available)
    if gpu in ["auto", "nvidia"]:
        cmd = [
            "ffmpeg", "-y",
            "-hwaccel", "cuda",
            "-hwaccel_output_format", "cuda",
            "-i", input_path,
            "-c:v", "libvpx-vp9",  # VP9 doesn't have hardware encoding, but we can decode with GPU
            "-deadline", "realtime",
            "-cpu-used", "8",
            "-crf", "35",
            "-b:v", "0",
            "-c:a", "libopus",
            "-b:a", "128k",
            output_path
        ]

        print("🎮 Trying NVIDIA CUDA acceleration...")
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            elapsed = time.time() - start_time
            output_size = os.path.getsize(output_path)
            print(f"✅ GPU acceleration successful! ({elapsed:.1f}s)")
            print(f"📊 {input_size:,} → {output_size:,} bytes")
            return True

    # Fallback to CPU-only ultra-fast mode
    print("💻 Falling back to CPU-only mode...")
    return convert_ultrafast(input_path, output_path)


def convert_direct_copy(input_path, output_path):
    """
    Direct stream copy to WebM container (fastest possible, no re-encoding).
    Only works if input codec is compatible with WebM.
    """
    print(f"⚡ DIRECT COPY mode (no re-encoding)")
    print(f"📥 Input: {input_path}")
    print(f"📤 Output: {output_path}")

    start_time = time.time()

    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-c:v", "copy",  # Copy video stream
        "-c:a", "copy",  # Copy audio stream
        output_path
    ]

    print("⏳ Copying streams...")
    result = subprocess.run(cmd, capture_output=True, text=True)

    elapsed = time.time() - start_time

    if result.returncode == 0:
        print(f"✅ Direct copy completed in {elapsed:.1f} seconds!")
        return True
    else:
        # If direct copy fails, try with re-encoding
        print("⚠️ Direct copy failed, trying fast re-encode...")
        return convert_ultrafast(input_path, output_path)


def batch_convert(input_dir, output_dir, pattern="*.mp4", method="ultrafast"):
    """
    Batch convert multiple files.

    Args:
        input_dir: Directory with input files
        output_dir: Directory for output files
        pattern: File pattern to match
        method: Conversion method
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    files = list(input_path.glob(pattern))
    print(f"📁 Found {len(files)} files to convert")

    successful = 0
    failed = 0

    for i, file in enumerate(files, 1):
        print(f"\n[{i}/{len(files)}] Processing: {file.name}")
        output_file = output_path / file.with_suffix('.webm').name

        if method == "ultrafast":
            success = convert_ultrafast(str(file), str(output_file))
        elif method == "hardware":
            success = convert_hardware_accelerated(str(file), str(output_file))
        elif method == "copy":
            success = convert_direct_copy(str(file), str(output_file))
        else:
            success = convert_ultrafast(str(file), str(output_file))

        if success:
            successful += 1
        else:
            failed += 1

    print(f"\n📊 Batch complete: {successful} successful, {failed} failed")


def main():
    parser = argparse.ArgumentParser(
        description='Ultra-Fast MP4 to WebM Converter',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Speed Comparison:
  🚀 copy      - Instant (no re-encoding, if compatible)
  🚀 ultrafast - ~5-10 seconds for typical videos
  🎮 hardware  - ~3-8 seconds (requires GPU)
  🐌 normal    - 30-120 seconds (better quality)

Examples:
  # Fastest possible (try direct copy first)
  python fast_convert.py input.mp4 output.webm --copy

  # Ultra-fast CPU encoding
  python fast_convert.py input.mp4 output.webm --ultrafast

  # Hardware acceleration (if available)
  python fast_convert.py input.mp4 output.webm --hardware

  # Batch conversion
  python fast_convert.py --batch input_dir/ output_dir/ --ultrafast

  # Custom quality (higher CRF = faster/lower quality)
  python fast_convert.py input.mp4 output.webm --crf 40
        '''
    )

    # Single file arguments
    parser.add_argument('input', nargs='?', help='Input MP4 file')
    parser.add_argument('output', nargs='?', help='Output WebM file')

    # Batch mode
    parser.add_argument('--batch', nargs=2, metavar=('INPUT_DIR', 'OUTPUT_DIR'),
                        help='Batch convert all MP4 files in directory')
    parser.add_argument('--pattern', default='*.mp4',
                        help='File pattern for batch mode (default: *.mp4)')

    # Conversion methods
    parser.add_argument('--ultrafast', action='store_true',
                        help='Use ultra-fast encoding settings')
    parser.add_argument('--hardware', action='store_true',
                        help='Try hardware acceleration (GPU)')
    parser.add_argument('--copy', action='store_true',
                        help='Try direct stream copy (fastest if compatible)')

    # Quality settings
    parser.add_argument('--crf', type=int, default=35,
                        help='CRF quality (0-63, default: 35, higher=faster/lower quality)')
    parser.add_argument('--preset', default='ultrafast',
                        choices=['ultrafast', 'superfast', 'veryfast', 'faster', 'fast'],
                        help='Encoding speed preset')

    args = parser.parse_args()

    # Batch mode
    if args.batch:
        method = "copy" if args.copy else "hardware" if args.hardware else "ultrafast"
        batch_convert(args.batch[0], args.batch[1], args.pattern, method)
        sys.exit(0)

    # Single file mode
    if not args.input:
        parser.print_help()
        sys.exit(1)

    if not os.path.exists(args.input):
        print(f"❌ Error: Input file not found: {args.input}")
        sys.exit(1)

    # Default output name if not specified
    if not args.output:
        args.output = Path(args.input).with_suffix('.webm')

    # Get video info (optional)
    info = get_video_info(args.input)
    if info:
        print(f"📹 Video info: {info.get('width')}x{info.get('height')}")

    # Choose conversion method
    success = False
    if args.copy:
        success = convert_direct_copy(args.input, args.output)
    elif args.hardware:
        success = convert_hardware_accelerated(args.input, args.output)
    else:
        success = convert_ultrafast(args.input, args.output, args.preset, args.crf)

    if success:
        print(f"🎉 Done! Output: {args.output}")
    else:
        print(f"❌ Conversion failed")
        sys.exit(1)


if __name__ == '__main__':
    main()