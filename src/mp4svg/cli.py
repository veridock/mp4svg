#!/usr/bin/env python3
"""
Command-line interface for mp4svg
"""

import argparse
import sys
import os

from . import (
    get_converter, list_converters, CONVERTER_REGISTRY,
    EncodingError, DecodingError
)


def main():
    """Command line interface for MP4 to SVG converters"""
    
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
  mp4svg video.mp4 output.svg --method polyglot
  mp4svg video.mp4 output.svg --method vector --max-frames 30
  mp4svg video.mp4 output_dir/ --method hybrid
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
            converter_class = get_converter('polyglot')
            converter = converter_class()
            converter.extract(args.input, args.output)
        elif args.method == 'ascii85':
            converter_class = get_converter('ascii85')
            converter = converter_class()
            converter.extract(args.input, args.output)
        else:
            print(f"Extraction not implemented for method: {args.method}")
        return

    # Handle conversion
    if args.method == 'polyglot':
        converter_class = get_converter('polyglot')
        converter = converter_class()
        converter.convert(args.input, args.output, args.pdf)

    elif args.method == 'ascii85':
        converter_class = get_converter('ascii85')
        converter = converter_class()
        converter.convert(args.input, args.output)

    elif args.method == 'vector':
        converter_class = get_converter('vector')
        converter = converter_class()
        converter.convert(args.input, args.output, args.max_frames, args.edge_threshold)

    elif args.method == 'qr':
        converter_class = get_converter('qrcode')
        converter = converter_class(chunk_size=args.chunk_size)
        converter.convert(args.input, args.output)

    elif args.method == 'hybrid':
        converter_class = get_converter('hybrid')
        converter = converter_class()
        converter.convert(args.input, args.output)

    else:
        available_methods = list_converters()
        print(f"Unknown method: {args.method}")
        print(f"Available methods: {', '.join(available_methods)}")
        sys.exit(1)


if __name__ == '__main__':
    main()
