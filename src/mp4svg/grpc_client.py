"""
gRPC Client for mp4svg
Client interface for connecting to and using mp4svg gRPC servers
"""

import asyncio
import logging
import time
from typing import Iterator, Optional, Dict, Any

import grpc
import grpc.aio

# Import the same mock classes as server (in production, these would be generated)
from .grpc_server import (
    ConvertVideoRequest, ConvertVideoResponse, ConvertVideoProgress,
    ExtractVideoRequest, ExtractVideoResponse,
    ValidateSVGRequest, ValidateSVGResponse,
    ValidateIntegrityRequest, ValidateIntegrityResponse,
    ListConvertersRequest, ListConvertersResponse,
    GetServerInfoRequest, GetServerInfoResponse
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MP4SVGClient:
    """gRPC Client for mp4svg video conversion services"""
    
    def __init__(self, server_address: str = "localhost:50051"):
        """Initialize gRPC client
        
        Args:
            server_address: Server address in format "host:port"
        """
        self.server_address = server_address
        self.channel = None
        self.stub = None
        
    def connect(self):
        """Connect to the gRPC server (synchronous)"""
        self.channel = grpc.insecure_channel(self.server_address)
        # In real implementation: self.stub = MP4SVGServiceStub(self.channel)
        logger.info(f"Connected to gRPC server at {self.server_address}")
        
    def disconnect(self):
        """Disconnect from the gRPC server (synchronous)"""
        if self.channel:
            self.channel.close()
        logger.info("Disconnected from gRPC server")
    
    async def connect_async(self):
        """Connect to the gRPC server (async)"""
        self.channel = grpc.aio.insecure_channel(self.server_address)
        # In real implementation: self.stub = MP4SVGServiceStub(self.channel)
        logger.info(f"Connected to async gRPC server at {self.server_address}")
    
    async def disconnect_async(self):
        """Disconnect from the gRPC server (async)"""
        if self.channel:
            await self.channel.close()
        logger.info("Disconnected from async gRPC server")
    
    def convert_video(self, input_path: str, output_path: str, method: str,
                     options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Convert MP4 video to SVG using specified method (synchronous)
        
        Args:
            input_path: Path to input MP4 file
            output_path: Path for output SVG file  
            method: Conversion method (ascii85, polyglot, vector, qrcode, hybrid)
            options: Method-specific options
            
        Returns:
            Conversion result dictionary
        """
        if not self.stub:
            raise RuntimeError("Not connected to server")
        
        request = ConvertVideoRequest()
        request.input_path = input_path
        request.output_path = output_path
        request.method = method
        
        # Set options if provided
        if options:
            # In real implementation, you'd populate the ConversionOptions message
            pass
        
        try:
            response = self.stub.ConvertVideo(request)
            
            return {
                "success": response.success,
                "message": response.message,
                "output_path": response.output_path,
                "input_size_bytes": response.input_size_bytes,
                "output_size_bytes": response.output_size_bytes,
                "compression_ratio": response.compression_ratio,
                "method_used": response.method_used,
                "processing_time_seconds": response.processing_time_seconds
            }
            
        except grpc.RpcError as e:
            logger.error(f"RPC error: {e}")
            return {
                "success": False,
                "message": f"RPC error: {e.details()}",
                "error_code": e.code()
            }
    
    async def convert_video_async(self, input_path: str, output_path: str, method: str,
                                options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Convert MP4 video to SVG using specified method (async)"""
        if not self.stub:
            raise RuntimeError("Not connected to server")
        
        request = ConvertVideoRequest()
        request.input_path = input_path
        request.output_path = output_path
        request.method = method
        
        try:
            response = await self.stub.ConvertVideo(request)
            
            return {
                "success": response.success,
                "message": response.message,
                "output_path": response.output_path,
                "input_size_bytes": response.input_size_bytes,
                "output_size_bytes": response.output_size_bytes,
                "compression_ratio": response.compression_ratio,
                "method_used": response.method_used,
                "processing_time_seconds": response.processing_time_seconds
            }
            
        except grpc.RpcError as e:
            logger.error(f"Async RPC error: {e}")
            return {
                "success": False,
                "message": f"RPC error: {e.details()}",
                "error_code": e.code()
            }
    
    def convert_video_stream(self, input_path: str, output_path: str, method: str,
                           options: Optional[Dict[str, Any]] = None) -> Iterator[Dict[str, Any]]:
        """Convert video with streaming progress updates (synchronous)"""
        if not self.stub:
            raise RuntimeError("Not connected to server")
        
        request = ConvertVideoRequest()
        request.input_path = input_path
        request.output_path = output_path
        request.method = method
        
        try:
            for progress in self.stub.ConvertVideoStream(request):
                yield {
                    "stage": progress.stage,
                    "progress_percent": progress.progress_percent,
                    "message": progress.message,
                    "completed": progress.completed
                }
                
        except grpc.RpcError as e:
            logger.error(f"Stream RPC error: {e}")
            yield {
                "stage": "Error",
                "progress_percent": 0,
                "message": f"RPC error: {e.details()}",
                "completed": True,
                "error_code": e.code()
            }
    
    async def convert_video_stream_async(self, input_path: str, output_path: str, method: str,
                                       options: Optional[Dict[str, Any]] = None):
        """Convert video with streaming progress updates (async)"""
        if not self.stub:
            raise RuntimeError("Not connected to server")
        
        request = ConvertVideoRequest()
        request.input_path = input_path
        request.output_path = output_path
        request.method = method
        
        try:
            async for progress in self.stub.ConvertVideoStream(request):
                yield {
                    "stage": progress.stage,
                    "progress_percent": progress.progress_percent,
                    "message": progress.message,
                    "completed": progress.completed
                }
                
        except grpc.RpcError as e:
            logger.error(f"Async stream RPC error: {e}")
            yield {
                "stage": "Error",
                "progress_percent": 0,
                "message": f"RPC error: {e.details()}",
                "completed": True,
                "error_code": e.code()
            }
    
    def extract_video(self, input_path: str, output_path: str, 
                     method: Optional[str] = None) -> Dict[str, Any]:
        """Extract MP4 video from SVG file (synchronous)"""
        if not self.stub:
            raise RuntimeError("Not connected to server")
        
        request = ExtractVideoRequest()
        request.input_path = input_path
        request.output_path = output_path
        if method:
            request.method = method
        
        try:
            response = self.stub.ExtractVideo(request)
            
            return {
                "success": response.success,
                "message": response.message,
                "output_path": response.output_path,
                "output_size_bytes": response.output_size_bytes,
                "method_detected": response.method_detected,
                "processing_time_seconds": response.processing_time_seconds
            }
            
        except grpc.RpcError as e:
            logger.error(f"Extract RPC error: {e}")
            return {
                "success": False,
                "message": f"RPC error: {e.details()}",
                "error_code": e.code()
            }
    
    async def extract_video_async(self, input_path: str, output_path: str,
                                method: Optional[str] = None) -> Dict[str, Any]:
        """Extract MP4 video from SVG file (async)"""
        if not self.stub:
            raise RuntimeError("Not connected to server")
        
        request = ExtractVideoRequest()
        request.input_path = input_path
        request.output_path = output_path
        if method:
            request.method = method
        
        try:
            response = await self.stub.ExtractVideo(request)
            
            return {
                "success": response.success,
                "message": response.message,
                "output_path": response.output_path,
                "output_size_bytes": response.output_size_bytes,
                "method_detected": response.method_detected,
                "processing_time_seconds": response.processing_time_seconds
            }
            
        except grpc.RpcError as e:
            logger.error(f"Async extract RPC error: {e}")
            return {
                "success": False,
                "message": f"RPC error: {e.details()}",
                "error_code": e.code()
            }
    
    def validate_svg(self, file_path: str) -> Dict[str, Any]:
        """Validate SVG file and detect mp4svg format (synchronous)"""
        if not self.stub:
            raise RuntimeError("Not connected to server")
        
        request = ValidateSVGRequest()
        request.file_path = file_path
        
        try:
            response = self.stub.ValidateSVG(request)
            
            return {
                "is_valid": response.is_valid,
                "detected_format": response.detected_format,
                "errors": list(response.errors),
                "warnings": list(response.warnings),
                "metadata": response.metadata  # Would be converted from protobuf
            }
            
        except grpc.RpcError as e:
            logger.error(f"Validate SVG RPC error: {e}")
            return {
                "is_valid": False,
                "errors": [f"RPC error: {e.details()}"],
                "error_code": e.code()
            }
    
    async def validate_svg_async(self, file_path: str) -> Dict[str, Any]:
        """Validate SVG file and detect mp4svg format (async)"""
        if not self.stub:
            raise RuntimeError("Not connected to server")
        
        request = ValidateSVGRequest()
        request.file_path = file_path
        
        try:
            response = await self.stub.ValidateSVG(request)
            
            return {
                "is_valid": response.is_valid,
                "detected_format": response.detected_format,
                "errors": list(response.errors),
                "warnings": list(response.warnings),
                "metadata": response.metadata
            }
            
        except grpc.RpcError as e:
            logger.error(f"Async validate SVG RPC error: {e}")
            return {
                "is_valid": False,
                "errors": [f"RPC error: {e.details()}"],
                "error_code": e.code()
            }
    
    def validate_integrity(self, original_path: str, svg_path: str, 
                         method: str) -> Dict[str, Any]:
        """Validate conversion roundtrip integrity (synchronous)"""
        if not self.stub:
            raise RuntimeError("Not connected to server")
        
        request = ValidateIntegrityRequest()
        request.original_path = original_path
        request.svg_path = svg_path
        request.method = method
        
        try:
            response = self.stub.ValidateIntegrity(request)
            
            return {
                "integrity_valid": response.integrity_valid,
                "message": response.message,
                "similarity_score": response.similarity_score,
                "metrics": response.metrics  # Would be converted from protobuf
            }
            
        except grpc.RpcError as e:
            logger.error(f"Validate integrity RPC error: {e}")
            return {
                "integrity_valid": False,
                "message": f"RPC error: {e.details()}",
                "error_code": e.code()
            }
    
    def list_converters(self) -> Dict[str, Any]:
        """List all available conversion methods (synchronous)"""
        if not self.stub:
            raise RuntimeError("Not connected to server")
        
        request = ListConvertersRequest()
        
        try:
            response = self.stub.ListConverters(request)
            
            converters = []
            for converter_info in response.converters:
                converters.append({
                    "name": converter_info.name,
                    "description": converter_info.description,
                    "supported_operations": list(converter_info.supported_operations),
                    "supports_streaming": converter_info.supports_streaming,
                    "capabilities": converter_info.capabilities  # Would be converted
                })
            
            return {
                "converters": converters,
                "total_count": response.total_count
            }
            
        except grpc.RpcError as e:
            logger.error(f"List converters RPC error: {e}")
            return {
                "converters": [],
                "total_count": 0,
                "error": f"RPC error: {e.details()}",
                "error_code": e.code()
            }
    
    def get_server_info(self) -> Dict[str, Any]:
        """Get server information and statistics (synchronous)"""
        if not self.stub:
            raise RuntimeError("Not connected to server")
        
        request = GetServerInfoRequest()
        
        try:
            response = self.stub.GetServerInfo(request)
            
            return {
                "server_name": response.server_name,
                "version": response.version,
                "build_time": response.build_time,
                "supported_formats": list(response.supported_formats),
                "capabilities": response.capabilities,  # Would be converted
                "stats": response.stats  # Would be converted
            }
            
        except grpc.RpcError as e:
            logger.error(f"Get server info RPC error: {e}")
            return {
                "server_name": "unknown",
                "error": f"RPC error: {e.details()}",
                "error_code": e.code()
            }

class MP4SVGClientCLI:
    """Command-line interface for gRPC client"""
    
    def __init__(self, server_address: str = "localhost:50051"):
        self.client = MP4SVGClient(server_address)
        self.connected = False
    
    def run_interactive(self):
        """Run interactive gRPC client session"""
        print("🚀 MP4SVG gRPC Client - Interactive Mode")
        print(f"Connecting to server at {self.client.server_address}...")
        
        try:
            self.client.connect()
            self.connected = True
            print("✅ Connected to mp4svg gRPC server\n")
            
            # Show server info
            server_info = self.client.get_server_info()
            if "error" not in server_info:
                print(f"📊 Server: {server_info['server_name']} v{server_info['version']}")
                print(f"📋 Supported formats: {', '.join(server_info['supported_formats'])}")
                print()
            
            # Interactive loop
            while True:
                try:
                    command = input("grpc> ").strip()
                    if not command:
                        continue
                    
                    if command in ["exit", "quit", "q"]:
                        break
                    elif command == "help":
                        self.show_help()
                    elif command == "info":
                        self.show_server_info()
                    elif command == "converters":
                        self.show_converters()
                    elif command.startswith("convert "):
                        self.handle_convert(command)
                    elif command.startswith("convert-stream "):
                        self.handle_convert_stream(command)
                    elif command.startswith("extract "):
                        self.handle_extract(command)
                    elif command.startswith("validate "):
                        self.handle_validate(command)
                    else:
                        print("Unknown command. Type 'help' for available commands.")
                        
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    print(f"❌ Error: {e}")
            
        except Exception as e:
            print(f"❌ Failed to connect: {e}")
        finally:
            if self.connected:
                self.client.disconnect()
                print("👋 Disconnected from server")
    
    def show_help(self):
        """Show help information"""
        print("""
📖 Available commands:
  help                        - Show this help
  info                        - Show server information
  converters                  - List available converters
  convert <args>              - Convert video (format: input.mp4 output.svg method [options])
  convert-stream <args>       - Convert with streaming progress
  extract <args>              - Extract video (format: input.svg output.mp4 [method])
  validate <file>             - Validate SVG file
  exit/quit/q                - Exit client
        """)
    
    def show_server_info(self):
        """Show server information"""
        info = self.client.get_server_info()
        if "error" in info:
            print(f"❌ Error getting server info: {info['error']}")
        else:
            print(f"🖥️  Server Information:")
            print(f"   Name: {info['server_name']}")
            print(f"   Version: {info['version']}")
            print(f"   Build Time: {info['build_time']}")
            print(f"   Supported Formats: {', '.join(info['supported_formats'])}")
            print()
    
    def show_converters(self):
        """Show available converters"""
        result = self.client.list_converters()
        if "error" in result:
            print(f"❌ Error getting converters: {result['error']}")
        else:
            print(f"🔄 Available converters ({result['total_count']}):")
            for converter in result['converters']:
                print(f"  • {converter['name']}: {converter['description']}")
                print(f"    Operations: {', '.join(converter['supported_operations'])}")
                print(f"    Streaming: {'Yes' if converter['supports_streaming'] else 'No'}")
                print()
    
    def handle_convert(self, command: str):
        """Handle convert command"""
        parts = command.split()[1:]  # Remove 'convert'
        if len(parts) < 3:
            print("Usage: convert <input.mp4> <output.svg> <method> [options]")
            return
        
        input_path, output_path, method = parts[:3]
        options = {}
        
        # Parse simple options (key=value)
        for part in parts[3:]:
            if '=' in part:
                key, value = part.split('=', 1)
                try:
                    if '.' in value:
                        options[key] = float(value)
                    else:
                        options[key] = int(value)
                except ValueError:
                    options[key] = value
        
        print(f"🔄 Converting {input_path} → {output_path} using {method}...")
        result = self.client.convert_video(input_path, output_path, method, options)
        
        if result.get("success"):
            print(f"✅ Conversion successful!")
            print(f"   Input size: {result['input_size_bytes']:,} bytes")
            print(f"   Output size: {result['output_size_bytes']:,} bytes")
            print(f"   Compression ratio: {result['compression_ratio']}")
            print(f"   Processing time: {result['processing_time_seconds']:.2f}s")
        else:
            print(f"❌ Conversion failed: {result.get('message', 'Unknown error')}")
    
    def handle_convert_stream(self, command: str):
        """Handle streaming convert command"""
        parts = command.split()[1:]  # Remove 'convert-stream'
        if len(parts) < 3:
            print("Usage: convert-stream <input.mp4> <output.svg> <method>")
            return
        
        input_path, output_path, method = parts[:3]
        
        print(f"🔄 Converting {input_path} → {output_path} using {method} (streaming)...")
        
        for progress in self.client.convert_video_stream(input_path, output_path, method):
            if "error_code" in progress:
                print(f"❌ Error: {progress['message']}")
                break
            
            print(f"   {progress['stage']}: {progress['progress_percent']:.1f}% - {progress['message']}")
            
            if progress['completed']:
                if progress['progress_percent'] == 100:
                    print("✅ Conversion completed!")
                break
    
    def handle_extract(self, command: str):
        """Handle extract command"""
        parts = command.split()[1:]  # Remove 'extract'
        if len(parts) < 2:
            print("Usage: extract <input.svg> <output.mp4> [method]")
            return
        
        input_path, output_path = parts[:2]
        method = parts[2] if len(parts) > 2 else None
        
        print(f"📤 Extracting {input_path} → {output_path}...")
        result = self.client.extract_video(input_path, output_path, method)
        
        if result.get("success"):
            print(f"✅ Extraction successful!")
            print(f"   Method detected: {result['method_detected']}")
            print(f"   Output size: {result['output_size_bytes']:,} bytes")
            print(f"   Processing time: {result['processing_time_seconds']:.2f}s")
        else:
            print(f"❌ Extraction failed: {result.get('message', 'Unknown error')}")
    
    def handle_validate(self, command: str):
        """Handle validate command"""
        parts = command.split()[1:]  # Remove 'validate'
        if len(parts) < 1:
            print("Usage: validate <file.svg>")
            return
        
        file_path = parts[0]
        print(f"🔍 Validating {file_path}...")
        result = self.client.validate_svg(file_path)
        
        if "error_code" in result:
            print(f"❌ Validation error: {result.get('message', 'Unknown error')}")
        else:
            print(f"📊 Validation results:")
            print(f"   Valid: {result['is_valid']}")
            print(f"   Format: {result.get('detected_format', 'Unknown')}")
            if result.get('errors'):
                print(f"   Errors: {len(result['errors'])}")
                for error in result['errors']:
                    print(f"     - {error}")
            if result.get('warnings'):
                print(f"   Warnings: {len(result['warnings'])}")
                for warning in result['warnings']:
                    print(f"     - {warning}")

def main():
    """Main entry point for gRPC client CLI"""
    import argparse
    
    parser = argparse.ArgumentParser(description="MP4SVG gRPC Client")
    parser.add_argument("--server", default="localhost:50051",
                       help="Server address (host:port)")
    parser.add_argument("--interactive", "-i", action="store_true",
                       help="Run in interactive mode")
    
    # Tool-specific commands
    parser.add_argument("--convert", nargs=3, metavar=("INPUT", "OUTPUT", "METHOD"),
                       help="Convert video: INPUT.mp4 OUTPUT.svg METHOD")
    parser.add_argument("--extract", nargs=2, metavar=("INPUT", "OUTPUT"),
                       help="Extract video: INPUT.svg OUTPUT.mp4")
    parser.add_argument("--validate", metavar="FILE",
                       help="Validate SVG file")
    parser.add_argument("--list-converters", action="store_true",
                       help="List available converters")
    parser.add_argument("--server-info", action="store_true",
                       help="Show server information")
    
    args = parser.parse_args()
    
    client_cli = MP4SVGClientCLI(args.server)
    
    if args.interactive:
        client_cli.run_interactive()
    else:
        # Handle individual commands
        try:
            client_cli.client.connect()
            
            if args.convert:
                input_path, output_path, method = args.convert
                result = client_cli.client.convert_video(input_path, output_path, method)
                print(f"Conversion result: {result}")
            
            elif args.extract:
                input_path, output_path = args.extract
                result = client_cli.client.extract_video(input_path, output_path)
                print(f"Extraction result: {result}")
            
            elif args.validate:
                result = client_cli.client.validate_svg(args.validate)
                print(f"Validation result: {result}")
            
            elif args.list_converters:
                result = client_cli.client.list_converters()
                print(f"Available converters: {result}")
            
            elif args.server_info:
                result = client_cli.client.get_server_info()
                print(f"Server info: {result}")
            
            else:
                parser.print_help()
        
        finally:
            client_cli.client.disconnect()

if __name__ == "__main__":
    main()
