"""
Interactive CLI shell for mp4svg
Provides a command-line interface with tab completion, history, and interactive features
"""

import os
import sys
import cmd
import shlex
import readline
import atexit
import tempfile
from pathlib import Path
from typing import Optional, List, Dict, Any

from . import (
    ASCII85SVGConverter, PolyglotSVGConverter, SVGVectorFrameConverter,
    QRCodeSVGConverter, HybridSVGConverter
)
from .validators import SVGValidator, IntegrityValidator
from .base import EncodingError, DecodingError


class MP4SVGShell(cmd.Cmd):
    """Interactive shell for mp4svg operations"""
    
    intro = '''
╔═══════════════════════════════════════════════════════════════════════════════╗
║                            MP4SVG Interactive Shell                           ║
║                                                                               ║
║  Convert MP4 videos to SVG containers using multiple encoding methods.       ║
║  Type 'help' or '?' to list commands. Type 'help <command>' for details.     ║
╚═══════════════════════════════════════════════════════════════════════════════╝
    '''
    
    prompt = '(mp4svg) '
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Initialize converters
        self.converters = {
            'ascii85': ASCII85SVGConverter(),
            'polyglot': PolyglotSVGConverter(),
            'vector': SVGVectorFrameConverter(),
            'qrcode': QRCodeSVGConverter(),
            'hybrid': HybridSVGConverter()
        }
        
        # Initialize validators
        self.svg_validator = SVGValidator()
        self.integrity_validator = IntegrityValidator()
        
        # Shell state
        self.current_method = 'ascii85'
        self.output_dir = os.getcwd()
        self.last_converted = None
        self.conversion_history = []
        
        # Setup command history
        self._setup_history()
        
        # Available methods for tab completion
        self.methods = list(self.converters.keys())
    
    def _setup_history(self):
        """Setup command history persistence"""
        history_file = os.path.expanduser('~/.mp4svg_history')
        
        try:
            readline.read_history_file(history_file)
        except FileNotFoundError:
            pass
        
        atexit.register(readline.write_history_file, history_file)
        
        # Set history length
        readline.set_history_length(1000)
    
    def cmdloop(self, intro=None):
        """Override cmdloop to handle keyboard interrupts gracefully"""
        try:
            super().cmdloop(intro)
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            return
    
    def emptyline(self):
        """Override to do nothing on empty line"""
        pass
    
    def do_convert(self, args):
        """
        Convert MP4 to SVG using specified method.
        
        Usage: convert <input.mp4> [output.svg] [--method METHOD] [--options...]
        
        Methods: ascii85 (default), polyglot, vector, qrcode, hybrid
        
        Examples:
          convert video.mp4
          convert video.mp4 output.svg --method polyglot
          convert video.mp4 --method qrcode --chunk-size 1000
        """
        try:
            parsed_args = self._parse_convert_args(args)
            if not parsed_args:
                return
                
            input_file, output_file, method, options = parsed_args
            
            # Validate input file
            if not os.path.exists(input_file):
                print(f"❌ Input file not found: {input_file}")
                return
            
            # Get converter
            converter = self.converters[method]
            
            # Apply options to converter
            self._apply_converter_options(converter, options)
            
            print(f"🔄 Converting {input_file} using {method} method...")
            
            # Perform conversion
            result = converter.convert(input_file, output_file)
            
            if result:
                file_size = os.path.getsize(result) / (1024 * 1024)  # MB
                print(f"✅ Conversion successful!")
                print(f"   Output: {result}")
                print(f"   Size: {file_size:.2f} MB")
                
                # Update state
                self.last_converted = result
                self.conversion_history.append({
                    'input': input_file,
                    'output': result,
                    'method': method,
                    'size_mb': file_size
                })
            else:
                print("❌ Conversion failed")
                
        except (EncodingError, DecodingError) as e:
            print(f"❌ Conversion error: {e}")
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
    
    def do_extract(self, args):
        """
        Extract MP4 from SVG file.
        
        Usage: extract <input.svg> [output.mp4]
        
        Examples:
          extract output.svg
          extract output.svg extracted.mp4
        """
        try:
            args_list = shlex.split(args)
            
            if not args_list:
                if self.last_converted:
                    svg_file = self.last_converted
                else:
                    print("❌ Please specify SVG file to extract from")
                    return
            else:
                svg_file = args_list[0]
            
            if not os.path.exists(svg_file):
                print(f"❌ SVG file not found: {svg_file}")
                return
            
            # Generate output filename
            if len(args_list) > 1:
                output_file = args_list[1]
            else:
                base_name = os.path.splitext(os.path.basename(svg_file))[0]
                output_file = os.path.join(self.output_dir, f"{base_name}_extracted.mp4")
            
            print(f"🔄 Extracting MP4 from {svg_file}...")
            
            # Try each converter to find the right format
            success = False
            for method_name, converter in self.converters.items():
                if hasattr(converter, 'extract'):
                    try:
                        result = converter.extract(svg_file, output_file)
                        if result:
                            success = True
                            print(f"✅ Extraction successful using {method_name} method!")
                            print(f"   Output: {output_file}")
                            file_size = os.path.getsize(output_file) / (1024 * 1024)
                            print(f"   Size: {file_size:.2f} MB")
                            break
                    except:
                        continue
            
            if not success:
                print("❌ Could not extract MP4 - format not recognized or extraction failed")
                
        except Exception as e:
            print(f"❌ Extraction error: {e}")
    
    def do_validate(self, args):
        """
        Validate SVG file structure and integrity.
        
        Usage: validate <svg_file> [original.mp4]
        
        Examples:
          validate output.svg
          validate output.svg original.mp4  # With integrity check
        """
        try:
            args_list = shlex.split(args)
            
            if not args_list:
                if self.last_converted:
                    svg_file = self.last_converted
                else:
                    print("❌ Please specify SVG file to validate")
                    return
            else:
                svg_file = args_list[0]
            
            if not os.path.exists(svg_file):
                print(f"❌ SVG file not found: {svg_file}")
                return
            
            original_mp4 = args_list[1] if len(args_list) > 1 else None
            
            print(f"🔍 Validating {svg_file}...")
            
            # SVG structure validation
            svg_result = self.svg_validator.validate_svg_file(svg_file)
            
            print(f"\n📋 SVG Validation Results:")
            print(f"   Well-formed XML: {'✅' if svg_result['is_well_formed'] else '❌'}")
            print(f"   Format detected: {svg_result.get('detected_format', 'Unknown')}")
            
            if svg_result.get('metadata'):
                print(f"   Metadata: {svg_result['metadata']}")
            
            if svg_result['errors']:
                print("   ❌ Errors:")
                for error in svg_result['errors']:
                    print(f"      • {error}")
            
            if svg_result['warnings']:
                print("   ⚠️  Warnings:")
                for warning in svg_result['warnings']:
                    print(f"      • {warning}")
            
            # Integrity validation
            integrity_result = self.integrity_validator.validate_integrity(
                svg_file, original_mp4
            )
            
            print(f"\n🔒 Integrity Validation:")
            print(f"   Extraction successful: {'✅' if integrity_result['extraction_successful'] else '❌'}")
            
            if original_mp4:
                print(f"   Data integrity: {'✅' if integrity_result.get('data_integrity_valid') else '❌'}")
                print(f"   Checksum match: {'✅' if integrity_result.get('checksum_match') else '❌'}")
            
            if integrity_result['errors']:
                print("   ❌ Errors:")
                for error in integrity_result['errors']:
                    print(f"      • {error}")
            
        except Exception as e:
            print(f"❌ Validation error: {e}")
    
    def do_method(self, method_name):
        """
        Set default conversion method.
        
        Usage: method [METHOD_NAME]
        
        Available methods: ascii85, polyglot, vector, qrcode, hybrid
        
        Examples:
          method           # Show current method
          method ascii85   # Set method to ascii85
        """
        if not method_name:
            print(f"Current method: {self.current_method}")
            print(f"Available methods: {', '.join(self.methods)}")
            return
        
        if method_name in self.methods:
            self.current_method = method_name
            print(f"✅ Default method set to: {method_name}")
        else:
            print(f"❌ Unknown method: {method_name}")
            print(f"Available methods: {', '.join(self.methods)}")
    
    def do_status(self, args):
        """
        Show current shell status and recent conversions.
        
        Usage: status
        """
        print(f"\n📊 MP4SVG Shell Status:")
        print(f"   Current method: {self.current_method}")
        print(f"   Output directory: {self.output_dir}")
        print(f"   Last converted: {self.last_converted or 'None'}")
        
        if self.conversion_history:
            print(f"\n📝 Recent Conversions ({len(self.conversion_history)} total):")
            for i, conv in enumerate(self.conversion_history[-5:], 1):  # Show last 5
                print(f"   {i}. {conv['input']} → {conv['output']}")
                print(f"      Method: {conv['method']}, Size: {conv['size_mb']:.2f} MB")
    
    def do_cd(self, path):
        """
        Change output directory.
        
        Usage: cd <path>
        
        Examples:
          cd /path/to/output
          cd ..
          cd ~
        """
        if not path:
            path = os.path.expanduser('~')
        
        path = os.path.expanduser(path)
        
        try:
            if os.path.isdir(path):
                self.output_dir = os.path.abspath(path)
                print(f"✅ Changed directory to: {self.output_dir}")
            else:
                print(f"❌ Directory not found: {path}")
        except Exception as e:
            print(f"❌ Error changing directory: {e}")
    
    def do_ls(self, args):
        """
        List files in current output directory.
        
        Usage: ls [pattern]
        
        Examples:
          ls          # List all files
          ls *.svg    # List SVG files
          ls *.mp4    # List MP4 files
        """
        import glob
        
        pattern = args.strip() or '*'
        
        try:
            files = glob.glob(os.path.join(self.output_dir, pattern))
            files = sorted([f for f in files if os.path.isfile(f)])
            
            if files:
                print(f"\n📁 Files in {self.output_dir}:")
                for file_path in files:
                    filename = os.path.basename(file_path)
                    size = os.path.getsize(file_path)
                    size_str = self._format_file_size(size)
                    print(f"   {filename} ({size_str})")
            else:
                print(f"No files matching '{pattern}' found in {self.output_dir}")
                
        except Exception as e:
            print(f"❌ Error listing files: {e}")
    
    def do_info(self, args):
        """
        Show information about a file.
        
        Usage: info <filename>
        
        Examples:
          info video.mp4
          info output.svg
        """
        if not args:
            print("❌ Please specify a filename")
            return
        
        filepath = args.strip()
        if not os.path.isabs(filepath):
            filepath = os.path.join(self.output_dir, filepath)
        
        if not os.path.exists(filepath):
            print(f"❌ File not found: {filepath}")
            return
        
        try:
            stat = os.stat(filepath)
            size = self._format_file_size(stat.st_size)
            
            print(f"\n📄 File Information: {os.path.basename(filepath)}")
            print(f"   Path: {filepath}")
            print(f"   Size: {size}")
            print(f"   Modified: {self._format_timestamp(stat.st_mtime)}")
            
            # If it's an SVG, try to detect format
            if filepath.endswith('.svg'):
                try:
                    svg_result = self.svg_validator.validate_svg_file(filepath)
                    print(f"   SVG Format: {svg_result.get('detected_format', 'Unknown')}")
                    if svg_result.get('metadata'):
                        print(f"   Metadata: {svg_result['metadata']}")
                except:
                    pass
                    
        except Exception as e:
            print(f"❌ Error getting file info: {e}")
    
    def do_batch(self, args):
        """
        Batch convert all MP4 files in a directory.
        
        Usage: batch <input_dir> [output_dir] [--method METHOD]
        
        Examples:
          batch /path/to/videos
          batch /path/to/videos /path/to/output --method polyglot
        """
        try:
            args_list = shlex.split(args)
            
            if not args_list:
                print("❌ Please specify input directory")
                return
            
            input_dir = args_list[0]
            output_dir = args_list[1] if len(args_list) > 1 else self.output_dir
            
            # Parse method option
            method = self.current_method
            if '--method' in args_list:
                method_idx = args_list.index('--method')
                if method_idx + 1 < len(args_list):
                    method = args_list[method_idx + 1]
            
            if not os.path.isdir(input_dir):
                print(f"❌ Input directory not found: {input_dir}")
                return
            
            # Find all MP4 files
            mp4_files = []
            for filename in os.listdir(input_dir):
                if filename.lower().endswith('.mp4'):
                    mp4_files.append(os.path.join(input_dir, filename))
            
            if not mp4_files:
                print(f"No MP4 files found in {input_dir}")
                return
            
            print(f"🔄 Batch converting {len(mp4_files)} MP4 files using {method} method...")
            
            converter = self.converters[method]
            success_count = 0
            
            for i, mp4_file in enumerate(mp4_files, 1):
                filename = os.path.basename(mp4_file)
                svg_filename = filename.replace('.mp4', '.svg')
                svg_path = os.path.join(output_dir, svg_filename)
                
                print(f"[{i}/{len(mp4_files)}] Converting {filename}...")
                
                try:
                    result = converter.convert(mp4_file, svg_path)
                    if result:
                        success_count += 1
                        print(f"   ✅ Success: {svg_filename}")
                    else:
                        print(f"   ❌ Failed: {filename}")
                except Exception as e:
                    print(f"   ❌ Error: {filename} - {e}")
            
            print(f"\n📊 Batch conversion complete: {success_count}/{len(mp4_files)} successful")
            
        except Exception as e:
            print(f"❌ Batch conversion error: {e}")
    
    def do_clear(self, args):
        """Clear the screen"""
        os.system('clear' if os.name == 'posix' else 'cls')
    
    def do_quit(self, args):
        """Exit the shell"""
        print("Goodbye! 👋")
        return True
    
    def do_exit(self, args):
        """Exit the shell"""
        return self.do_quit(args)
    
    # Tab completion methods
    def complete_method(self, text, line, begidx, endidx):
        """Tab completion for method command"""
        return [method for method in self.methods if method.startswith(text)]
    
    def complete_convert(self, text, line, begidx, endidx):
        """Tab completion for convert command"""
        return self._complete_filename(text, line, begidx, endidx)
    
    def complete_extract(self, text, line, begidx, endidx):
        """Tab completion for extract command"""
        return self._complete_filename(text, line, begidx, endidx)
    
    def complete_validate(self, text, line, begidx, endidx):
        """Tab completion for validate command"""
        return self._complete_filename(text, line, begidx, endidx)
    
    def complete_info(self, text, line, begidx, endidx):
        """Tab completion for info command"""
        return self._complete_filename(text, line, begidx, endidx)
    
    def _complete_filename(self, text, line, begidx, endidx):
        """Generic filename completion"""
        import glob
        
        if not text:
            completions = glob.glob(os.path.join(self.output_dir, '*'))
        else:
            completions = glob.glob(os.path.expanduser(text) + '*')
        
        return [os.path.basename(path) for path in completions if os.path.isfile(path)]
    
    def _parse_convert_args(self, args):
        """Parse convert command arguments"""
        try:
            args_list = shlex.split(args)
            
            if not args_list:
                print("❌ Please specify input MP4 file")
                return None
            
            input_file = args_list[0]
            
            # Generate output filename if not specified
            if len(args_list) > 1 and not args_list[1].startswith('--'):
                output_file = args_list[1]
                options_start = 2
            else:
                base_name = os.path.splitext(os.path.basename(input_file))[0]
                output_file = os.path.join(self.output_dir, f"{base_name}.svg")
                options_start = 1
            
            # Parse method
            method = self.current_method
            options = {}
            
            i = options_start
            while i < len(args_list):
                arg = args_list[i]
                if arg == '--method' and i + 1 < len(args_list):
                    method = args_list[i + 1]
                    i += 2
                elif arg == '--chunk-size' and i + 1 < len(args_list):
                    options['chunk_size'] = int(args_list[i + 1])
                    i += 2
                else:
                    i += 1
            
            if method not in self.methods:
                print(f"❌ Unknown method: {method}")
                return None
            
            return input_file, output_file, method, options
            
        except Exception as e:
            print(f"❌ Error parsing arguments: {e}")
            return None
    
    def _apply_converter_options(self, converter, options):
        """Apply options to converter instance"""
        for key, value in options.items():
            if hasattr(converter, key):
                setattr(converter, key, value)
    
    def _format_file_size(self, size_bytes):
        """Format file size in human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
    
    def _format_timestamp(self, timestamp):
        """Format timestamp in readable format"""
        import datetime
        return datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')


def main():
    """Entry point for interactive shell"""
    shell = MP4SVGShell()
    shell.cmdloop()


if __name__ == '__main__':
    main()
