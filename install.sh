#!/bin/bash
# ============================================
# MP4 to SVG Converter Suite - Setup & Usage
# ============================================

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}MP4 to SVG Converter Suite - Setup${NC}"
echo -e "${BLUE}============================================${NC}\n"

# ============================================
# 1. Installation Script
# ============================================

install_dependencies() {
    echo -e "${YELLOW}Installing Python dependencies...${NC}"

    # Create requirements.txt
    cat > requirements.txt << 'EOF'
opencv-python>=4.8.0
numpy>=1.24.0
Pillow>=10.0.0
qrcode>=7.4.0
lxml>=4.9.0
EOF

    # Install with pip
    pip install -r requirements.txt

    # Check for system dependencies
    echo -e "\n${YELLOW}Checking system dependencies...${NC}"

    # Check for FFmpeg (optional but recommended)
    if command -v ffmpeg &> /dev/null; then
        echo -e "${GREEN}✓ FFmpeg found${NC}"
    else
        echo -e "${RED}✗ FFmpeg not found (optional, but recommended for better video processing)${NC}"
        echo "  Install with: sudo apt-get install ffmpeg  # Ubuntu/Debian"
        echo "               brew install ffmpeg           # macOS"
    fi

    # Check for ImageMagick (optional for advanced conversions)
    if command -v convert &> /dev/null; then
        echo -e "${GREEN}✓ ImageMagick found${NC}"
    else
        echo -e "${RED}✗ ImageMagick not found (optional)${NC}"
        echo "  Install with: sudo apt-get install imagemagick  # Ubuntu/Debian"
    fi

    echo -e "\n${GREEN}Dependencies installed!${NC}\n"
}

# ============================================
# 2. Test Script
# ============================================

create_test_video() {
    echo -e "${YELLOW}Creating test video...${NC}"

    # Create a simple test video using Python
    cat > create_test_video.py << 'EOF'
import cv2
import numpy as np

# Create test video
width, height = 640, 480
fps = 30
duration = 3  # seconds
fourcc = cv2.VideoWriter_fourcc(*'mp4v')

out = cv2.VideoWriter('test_video.mp4', fourcc, fps, (width, height))

for frame_num in range(fps * duration):
    # Create frame with moving circle
    frame = np.zeros((height, width, 3), dtype=np.uint8)

    # Animated background
    frame[:, :] = [20, 20, 30]

    # Moving circle
    x = int(width/2 + 200 * np.sin(frame_num * 0.1))
    y = int(height/2 + 100 * np.cos(frame_num * 0.1))
    cv2.circle(frame, (x, y), 30, (0, 255, 0), -1)

    # Frame counter
    cv2.putText(frame, f"Frame {frame_num}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

    out.write(frame)

out.release()
print("Created test_video.mp4")
EOF

    python create_test_video.py
    echo -e "${GREEN}Test video created: test_video.mp4${NC}\n"
}

# ============================================
# 3. Usage Examples
# ============================================

show_examples() {
    echo -e "${BLUE}============================================${NC}"
    echo -e "${BLUE}USAGE EXAMPLES${NC}"
    echo -e "${BLUE}============================================${NC}\n"

    echo -e "${YELLOW}1. POLYGLOT METHOD (Hide MP4 in SVG)${NC}"
    echo "   python mp4_to_svg.py video.mp4 output_polyglot.svg --method polyglot"
    echo "   # Extract back:"
    echo "   python mp4_to_svg.py output_polyglot.svg extracted.mp4 --method polyglot --extract"
    echo ""

    echo -e "${YELLOW}2. ASCII85 METHOD (25% overhead vs 33% for base64)${NC}"
    echo "   python mp4_to_svg.py video.mp4 output_ascii85.svg --method ascii85"
    echo ""

    echo -e "${YELLOW}3. VECTOR METHOD (Convert to SVG paths)${NC}"
    echo "   python mp4_to_svg.py video.mp4 output_vector.svg --method vector --max-frames 30"
    echo "   # With custom edge detection:"
    echo "   python mp4_to_svg.py video.mp4 output_vector.svg --method vector --edge-threshold 100"
    echo ""

    echo -e "${YELLOW}4. QR CODE METHOD (Memvid-style)${NC}"
    echo "   python mp4_to_svg.py video.mp4 output_qr.svg --method qr --chunk-size 2048"
    echo ""

    echo -e "${YELLOW}5. HYBRID METHOD (Try all and compare)${NC}"
    echo "   python mp4_to_svg.py video.mp4 output_dir/ --method hybrid"
    echo ""

    echo -e "${YELLOW}6. WITH PDF EMBEDDING (Polyglot only)${NC}"
    echo "   python mp4_to_svg.py video.mp4 output.svg --method polyglot --pdf document.pdf"
    echo ""
}

# ============================================
# 4. Benchmark Script
# ============================================

create_benchmark() {
    echo -e "${YELLOW}Creating benchmark script...${NC}"

    cat > benchmark.py << 'EOF'
#!/usr/bin/env python3
"""Benchmark all conversion methods"""

import os
import time
import sys
import subprocess
from pathlib import Path

def benchmark_method(video_file, method):
    """Benchmark a single method"""

    output = f"benchmark_{method}.svg"

    start_time = time.time()

    # Run converter
    cmd = [
        "python", "mp4_to_svg.py",
        video_file,
        output,
        "--method", method
    ]

    if method == "vector":
        cmd.extend(["--max-frames", "10"])

    result = subprocess.run(cmd, capture_output=True, text=True)

    elapsed = time.time() - start_time

    # Get file sizes
    if os.path.exists(output):
        output_size = os.path.getsize(output)

        # Check for gzipped version
        gz_size = 0
        if os.path.exists(output + ".gz"):
            gz_size = os.path.getsize(output + ".gz")
    else:
        output_size = 0
        gz_size = 0

    return {
        "method": method,
        "time": elapsed,
        "size": output_size,
        "gz_size": gz_size,
        "success": result.returncode == 0
    }

def main():
    if len(sys.argv) < 2:
        print("Usage: python benchmark.py <video.mp4>")
        sys.exit(1)

    video_file = sys.argv[1]
    original_size = os.path.getsize(video_file)

    methods = ["polyglot", "ascii85", "vector", "qr"]
    results = []

    print(f"\nBenchmarking {video_file} ({original_size:,} bytes)")
    print("=" * 60)

    for method in methods:
        print(f"Testing {method}...", end=" ")
        result = benchmark_method(video_file, method)
        results.append(result)

        if result["success"]:
            print(f"✓ {result['time']:.2f}s")
        else:
            print("✗ Failed")

    # Print results table
    print("\n" + "=" * 60)
    print("BENCHMARK RESULTS")
    print("=" * 60)
    print(f"{'Method':<12} {'Time':<8} {'Size':<12} {'Overhead':<10} {'Gzipped':<12}")
    print("-" * 60)

    for r in results:
        if r["success"]:
            overhead = (r["size"] / original_size - 1) * 100 if r["size"] > 0 else 0
            gz_info = f"{r['gz_size']:,}" if r["gz_size"] > 0 else "N/A"

            print(f"{r['method']:<12} {r['time']:<8.2f} {r['size']:<12,} "
                  f"{overhead:<+10.1f}% {gz_info:<12}")

    print("=" * 60)

if __name__ == "__main__":
    main()
EOF

    chmod +x benchmark.py
    echo -e "${GREEN}Benchmark script created: benchmark.py${NC}\n"
}

# ============================================
# 5. Integration with router.php
# ============================================

create_php_integration() {
    echo -e "${YELLOW}Creating PHP integration example...${NC}"

    cat > svg_video_handler.php << 'PHP'
<?php
/**
 * SVG Video Handler for router.php integration
 */

class SVGVideoHandler {
    private $converterPath = '/path/to/mp4_to_svg.py';

    public function processVideo($mp4Path, $method = 'polyglot') {
        $outputPath = tempnam(sys_get_temp_dir(), 'svg_') . '.svg';

        // Run Python converter
        $cmd = sprintf(
            'python %s %s %s --method %s 2>&1',
            escapeshellarg($this->converterPath),
            escapeshellarg($mp4Path),
            escapeshellarg($outputPath),
            escapeshellarg($method)
        );

        exec($cmd, $output, $returnCode);

        if ($returnCode === 0 && file_exists($outputPath)) {
            return file_get_contents($outputPath);
        }

        return false;
    }

    public function extractVideo($svgPath, $method = 'polyglot') {
        $outputPath = tempnam(sys_get_temp_dir(), 'mp4_') . '.mp4';

        // Run Python extractor
        $cmd = sprintf(
            'python %s %s %s --method %s --extract 2>&1',
            escapeshellarg($this->converterPath),
            escapeshellarg($svgPath),
            escapeshellarg($outputPath),
            escapeshellarg($method)
        );

        exec($cmd, $output, $returnCode);

        if ($returnCode === 0 && file_exists($outputPath)) {
            return $outputPath;
        }

        return false;
    }
}

// Usage in router.php:
if (preg_match('/\.svg$/', $uri) && file_exists($path)) {
    $handler = new SVGVideoHandler();

    // Check if SVG contains video data
    $content = file_get_contents($path);

    if (strpos($content, 'POLYGLOT_BOUNDARY') !== false) {
        // Extract and stream video
        $mp4Path = $handler->extractVideo($path);

        if ($mp4Path) {
            header('Content-Type: video/mp4');
            readfile($mp4Path);
            unlink($mp4Path);
            exit;
        }
    }

    // Normal SVG handling
    header('Content-Type: image/svg+xml');
    echo $content;
}
PHP

    echo -e "${GREEN}PHP integration created: svg_video_handler.php${NC}\n"
}

# ============================================
# 6. Batch Processing Script
# ============================================

create_batch_processor() {
    echo -e "${YELLOW}Creating batch processor...${NC}"

    cat > batch_convert.sh << 'BATCH'
#!/bin/bash
# Batch convert multiple MP4 files to SVG

METHOD=${1:-polyglot}
INPUT_DIR=${2:-.}
OUTPUT_DIR=${3:-svg_output}

mkdir -p "$OUTPUT_DIR"

echo "Converting all MP4 files in $INPUT_DIR using $METHOD method..."
echo "Output directory: $OUTPUT_DIR"
echo ""

for mp4 in "$INPUT_DIR"/*.mp4; do
    if [ -f "$mp4" ]; then
        basename=$(basename "$mp4" .mp4)
        output="$OUTPUT_DIR/${basename}_${METHOD}.svg"

        echo "Converting: $mp4 -> $output"
        python mp4_to_svg.py "$mp4" "$output" --method "$METHOD"
        echo ""
    fi
done

echo "Batch conversion complete!"

# Generate size report
echo ""
echo "Size Report:"
echo "============"
ls -lh "$OUTPUT_DIR"/*.svg 2>/dev/null
BATCH

    chmod +x batch_convert.sh
    echo -e "${GREEN}Batch processor created: batch_convert.sh${NC}\n"
}

# ============================================
# Main Menu
# ============================================

show_menu() {
    echo -e "${BLUE}============================================${NC}"
    echo -e "${BLUE}MP4 to SVG Converter Suite${NC}"
    echo -e "${BLUE}============================================${NC}\n"
    echo "1) Install dependencies"
    echo "2) Create test video"
    echo "3) Show usage examples"
    echo "4) Create benchmark script"
    echo "5) Create PHP integration"
    echo "6) Create batch processor"
    echo "7) Run all setup steps"
    echo "8) Exit"
    echo ""
    read -p "Select option: " choice

    case $choice in
        1) install_dependencies ;;
        2) create_test_video ;;
        3) show_examples ;;
        4) create_benchmark ;;
        5) create_php_integration ;;
        6) create_batch_processor ;;
        7)
            install_dependencies
            create_test_video
            create_benchmark
            create_php_integration
            create_batch_processor
            show_examples
            ;;
        8) exit 0 ;;
        *) echo "Invalid option" ;;
    esac
}

# ============================================
# Quick Test
# ============================================

quick_test() {
    echo -e "${YELLOW}Running quick test with all methods...${NC}\n"

    # Create test video if not exists
    if [ ! -f "test_video.mp4" ]; then
        create_test_video
    fi

    # Test each method
    for method in polyglot ascii85 vector qr; do
        echo -e "${BLUE}Testing $method method...${NC}"
        python mp4_to_svg.py test_video.mp4 "test_${method}.svg" --method "$method"

        if [ -f "test_${method}.svg" ]; then
            size=$(ls -lh "test_${method}.svg" | awk '{print $5}')
            echo -e "${GREEN}✓ Created test_${method}.svg (${size})${NC}\n"
        else
            echo -e "${RED}✗ Failed to create test_${method}.svg${NC}\n"
        fi
    done
}

# ============================================
# Main Execution
# ============================================

if [ "$1" == "--quick-test" ]; then
    quick_test
elif [ "$1" == "--install" ]; then
    install_dependencies
elif [ "$1" == "--examples" ]; then
    show_examples
else
    show_menu
fi