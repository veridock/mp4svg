"""
Hybrid converter that combines all encoding methods for optimal storage
"""

import os
from typing import Dict, Any
from .ascii85 import ASCII85SVGConverter
from .polyglot import PolyglotSVGConverter
from .vector import SVGVectorFrameConverter
from .qrcode import QRCodeSVGConverter
from .base import BaseConverter


class HybridSVGConverter(BaseConverter):
    """Combines multiple encoding methods for optimal storage"""

    def __init__(self):
        self.polyglot = PolyglotSVGConverter()
        self.ascii85 = ASCII85SVGConverter()
        self.vector = SVGVectorFrameConverter()
        self.qr = QRCodeSVGConverter()

    def convert(self, mp4_path: str, output_dir: str) -> str:
        """Convert using all methods and compare results"""
        
        self._validate_input(mp4_path)
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        base_name = os.path.splitext(os.path.basename(mp4_path))[0]
        results = {}

        print(f"[Hybrid] Converting {mp4_path} using all methods...")
        
        # Test all conversion methods
        methods = [
            ('polyglot', self.polyglot, f"{output_dir}/{base_name}_polyglot.svg"),
            ('ascii85', self.ascii85, f"{output_dir}/{base_name}_ascii85.svg"),
            ('vector', self.vector, f"{output_dir}/{base_name}_vector.svg"),
            ('qr', self.qr, f"{output_dir}/{base_name}_qr.svg")
        ]
        
        for method_name, converter, output_path in methods:
            try:
                print(f"\n[Hybrid] Testing {method_name} method...")
                
                if method_name == 'vector':
                    converter.convert(mp4_path, output_path, max_frames=30, edge_threshold=50)
                elif method_name == 'qr':
                    converter.convert(mp4_path, output_path, include_metadata=True)
                else:
                    converter.convert(mp4_path, output_path)
                
                # Get file size
                if os.path.exists(output_path):
                    file_size = os.path.getsize(output_path)
                    results[method_name] = {
                        'path': output_path,
                        'size': file_size,
                        'success': True
                    }
                else:
                    results[method_name] = {'success': False, 'error': 'Output file not created'}
                    
            except Exception as e:
                results[method_name] = {'success': False, 'error': str(e)}
                print(f"[Hybrid] {method_name} failed: {e}")

        # Print comparison
        self._print_comparison(mp4_path, results)
        
        # Return the directory containing all results
        return output_dir

    def extract(self, svg_path: str, output_mp4: str) -> bool:
        """Extract MP4 from SVG (try to detect format automatically)"""
        
        print(f"[Hybrid] Analyzing {svg_path} to detect format...")
        
        try:
            with open(svg_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Detect format based on content
            if 'POLYGLOT_BOUNDARY_' in content:
                print("[Hybrid] Detected polyglot format")
                return self.polyglot.extract(svg_path, output_mp4)
            
            elif 'encoding="ascii85"' in content:
                print("[Hybrid] Detected ASCII85 format")
                return self.ascii85.extract(svg_path, output_mp4)
            
            elif 'qr-frame-' in content:
                print("[Hybrid] Detected QR code format")
                return self.qr.extract(svg_path, output_mp4)
            
            elif '<path d=' in content and '<set attributeName=' in content:
                print("[Hybrid] Detected vector format")
                return self.vector.extract(svg_path, output_mp4)
            
            else:
                print("[Hybrid] Unable to detect SVG format")
                return False
                
        except Exception as e:
            print(f"[Hybrid] Format detection failed: {e}")
            return False

    def _print_comparison(self, mp4_path: str, results: Dict[str, Any]) -> None:
        """Print size comparison of all methods"""
        
        original_size = os.path.getsize(mp4_path)
        
        print("\n" + "="*70)
        print("HYBRID CONVERSION RESULTS")
        print("="*70)
        print(f"Original MP4: {original_size:,} bytes")
        print()
        
        # Sort by file size
        successful_results = {k: v for k, v in results.items() if v.get('success')}
        sorted_results = sorted(successful_results.items(), key=lambda x: x[1].get('size', float('inf')))
        
        for method_name, result in sorted_results:
            size = result['size']
            ratio = size / original_size
            overhead = (ratio - 1) * 100
            
            print(f"{method_name.upper():>8}: {size:>10,} bytes  ({ratio:>5.1f}x)  "
                  f"{'+'if overhead > 0 else ''}{overhead:>+6.1f}% overhead")
            
            if method_name == 'polyglot':
                print("         └─ Perfect fidelity, 0% SVG overhead")
            elif method_name == 'ascii85':
                print("         └─ Perfect fidelity, efficient encoding")
            elif method_name == 'vector':
                print("         └─ Lossy conversion, ~90% smaller with gzip")
            elif method_name == 'qr':
                print("         └─ Perfect fidelity, requires QR scanner")
        
        # Show failed methods
        failed_results = {k: v for k, v in results.items() if not v.get('success')}
        if failed_results:
            print("\nFAILED CONVERSIONS:")
            for method_name, result in failed_results.items():
                print(f"{method_name.upper():>8}: {result.get('error', 'Unknown error')}")
        
        print()
        
        # Recommendations
        if successful_results:
            best_method = sorted_results[0][0]
            print("RECOMMENDATIONS:")
            
            if best_method == 'polyglot':
                print("• POLYGLOT: Best for perfect fidelity with zero SVG overhead")
                print("• Use when SVG must remain valid and lightweight")
                
            elif best_method == 'ascii85':
                print("• ASCII85: Best balance of fidelity and XML compatibility")
                print("• Use for web embedding with thumbnail preview")
                
            elif best_method == 'vector':
                print("• VECTOR: Smallest file size (especially with compression)")
                print("• Use when approximate visual representation is acceptable")
                
            elif best_method == 'qr':
                print("• QR CODE: Unique visual presentation")
                print("• Use for interactive/artistic applications")
                
        print("="*70)
