"""
gRPC Server for mp4svg
Provides video conversion and SVG validation services over gRPC protocol
"""

import asyncio
import logging
import os
import time
from concurrent import futures
from pathlib import Path
from typing import Iterator

import grpc
import grpc.aio

from . import get_converter, list_converters, CONVERTER_REGISTRY
from .validators import SVGValidator, IntegrityValidator
from .base import EncodingError, DecodingError, ValidationError

# Import generated protobuf classes (these would be generated from mp4svg.proto)
# For now, I'll create the basic structure - in production you'd run:
# python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. mp4svg.proto

# Mock protobuf classes for demonstration (replace with generated code)
class ConvertVideoRequest:
    def __init__(self):
        self.input_path = ""
        self.output_path = ""
        self.method = ""
        self.options = None

class ConvertVideoResponse:
    def __init__(self):
        self.success = False
        self.message = ""
        self.output_path = ""
        self.input_size_bytes = 0
        self.output_size_bytes = 0
        self.compression_ratio = 0.0
        self.method_used = ""
        self.processing_time_seconds = 0.0

class ConvertVideoProgress:
    def __init__(self):
        self.stage = ""
        self.progress_percent = 0.0
        self.message = ""
        self.completed = False

class ExtractVideoRequest:
    def __init__(self):
        self.input_path = ""
        self.output_path = ""
        self.method = ""

class ExtractVideoResponse:
    def __init__(self):
        self.success = False
        self.message = ""
        self.output_path = ""
        self.output_size_bytes = 0
        self.method_detected = ""
        self.processing_time_seconds = 0.0

class ValidateSVGRequest:
    def __init__(self):
        self.file_path = ""

class ValidateSVGResponse:
    def __init__(self):
        self.is_valid = False
        self.detected_format = ""
        self.errors = []
        self.warnings = []
        self.metadata = None

class ValidateIntegrityRequest:
    def __init__(self):
        self.original_path = ""
        self.svg_path = ""
        self.method = ""

class ValidateIntegrityResponse:
    def __init__(self):
        self.integrity_valid = False
        self.message = ""
        self.similarity_score = 0.0
        self.metrics = None

class ListConvertersRequest:
    def __init__(self):
        pass

class ListConvertersResponse:
    def __init__(self):
        self.converters = []
        self.total_count = 0

class ConverterInfo:
    def __init__(self):
        self.name = ""
        self.description = ""
        self.supported_operations = []
        self.supports_streaming = False
        self.capabilities = None

class GetServerInfoRequest:
    def __init__(self):
        pass

class GetServerInfoResponse:
    def __init__(self):
        self.server_name = "mp4svg-grpc-server"
        self.version = "1.0.1"
        self.build_time = ""
        self.supported_formats = []
        self.capabilities = None
        self.stats = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MP4SVGServicer:
    """gRPC servicer implementation for MP4SVG service"""
    
    def __init__(self):
        """Initialize the servicer with converters and validators"""
        # Initialize converters
        self.converters = {}
        for name in list_converters():
            converter_class = get_converter(name)
            self.converters[name] = converter_class()
        
        # Initialize validators
        self.svg_validator = SVGValidator()
        self.integrity_validator = IntegrityValidator()
        
        # Server statistics
        self.stats = {
            'total_conversions': 0,
            'total_extractions': 0,
            'total_validations': 0,
            'start_time': time.time(),
            'active_jobs': 0
        }
        
        logger.info(f"Initialized MP4SVG gRPC servicer with {len(self.converters)} converters")
    
    def ConvertVideo(self, request: ConvertVideoRequest, context) -> ConvertVideoResponse:
        """Convert MP4 video to SVG using specified method"""
        start_time = time.time()
        response = ConvertVideoResponse()
        
        try:
            self.stats['active_jobs'] += 1
            logger.info(f"Converting {request.input_path} using {request.method}")
            
            # Validate inputs
            if not os.path.exists(request.input_path):
                response.success = False
                response.message = f"Input file not found: {request.input_path}"
                return response
            
            if request.method not in self.converters:
                response.success = False
                response.message = f"Unknown conversion method: {request.method}"
                return response
            
            # Get input file size
            input_size = os.path.getsize(request.input_path)
            
            # Get converter instance
            converter = self.converters[request.method]
            
            # Handle method-specific options
            if request.method == "qrcode" and hasattr(request.options, 'chunk_size'):
                converter_class = get_converter(request.method)
                converter = converter_class(chunk_size=request.options.chunk_size)
            
            # Perform conversion
            if request.method == "vector":
                max_frames = getattr(request.options, 'max_frames', 30)
                edge_threshold = getattr(request.options, 'edge_threshold', 50)
                result_path = converter.convert(request.input_path, request.output_path, 
                                              max_frames, edge_threshold)
            elif request.method == "polyglot":
                pdf = getattr(request.options, 'pdf', False)
                result_path = converter.convert(request.input_path, request.output_path, pdf)
            else:
                result_path = converter.convert(request.input_path, request.output_path)
            
            # Get output file size
            output_size = os.path.getsize(result_path)
            processing_time = time.time() - start_time
            
            # Populate response
            response.success = True
            response.message = "Conversion successful"
            response.output_path = result_path
            response.input_size_bytes = input_size
            response.output_size_bytes = output_size
            response.compression_ratio = output_size / input_size if input_size > 0 else 0
            response.method_used = request.method
            response.processing_time_seconds = processing_time
            
            self.stats['total_conversions'] += 1
            logger.info(f"Conversion completed in {processing_time:.2f}s")
            
        except Exception as e:
            response.success = False
            response.message = f"Conversion failed: {str(e)}"
            logger.error(f"Conversion error: {e}")
        
        finally:
            self.stats['active_jobs'] -= 1
        
        return response
    
    def ConvertVideoStream(self, request: ConvertVideoRequest, context) -> Iterator[ConvertVideoProgress]:
        """Stream conversion progress for long operations"""
        try:
            # Mock streaming progress - in real implementation, this would
            # integrate with converter progress callbacks
            progress_stages = [
                ("Initializing", 0),
                ("Loading video", 10),
                ("Processing frames", 30),
                ("Encoding data", 60),
                ("Generating SVG", 80),
                ("Finalizing", 95),
                ("Complete", 100)
            ]
            
            for stage, percent in progress_stages:
                progress = ConvertVideoProgress()
                progress.stage = stage
                progress.progress_percent = percent
                progress.message = f"{stage}... ({percent}%)"
                progress.completed = (percent == 100)
                
                yield progress
                
                # Simulate processing time
                time.sleep(0.5)
                
        except Exception as e:
            progress = ConvertVideoProgress()
            progress.stage = "Error"
            progress.progress_percent = 0
            progress.message = f"Error: {str(e)}"
            progress.completed = True
            yield progress
    
    def ExtractVideo(self, request: ExtractVideoRequest, context) -> ExtractVideoResponse:
        """Extract MP4 video from SVG file"""
        start_time = time.time()
        response = ExtractVideoResponse()
        
        try:
            self.stats['active_jobs'] += 1
            logger.info(f"Extracting video from {request.input_path}")
            
            # Validate input
            if not os.path.exists(request.input_path):
                response.success = False
                response.message = f"Input file not found: {request.input_path}"
                return response
            
            # Auto-detect method if not specified
            method = request.method
            if not method:
                svg_result = self.svg_validator.validate_svg_file(request.input_path)
                method = svg_result.get("detected_format")
                if not method:
                    response.success = False
                    response.message = "Could not auto-detect SVG format"
                    return response
            
            if method not in ["ascii85", "polyglot"]:
                response.success = False
                response.message = f"Extraction not supported for method: {method}"
                return response
            
            # Perform extraction
            converter = self.converters[method]
            success = converter.extract(request.input_path, request.output_path)
            
            if success and os.path.exists(request.output_path):
                output_size = os.path.getsize(request.output_path)
                processing_time = time.time() - start_time
                
                response.success = True
                response.message = "Extraction successful"
                response.output_path = request.output_path
                response.output_size_bytes = output_size
                response.method_detected = method
                response.processing_time_seconds = processing_time
                
                self.stats['total_extractions'] += 1
                logger.info(f"Extraction completed in {processing_time:.2f}s")
            else:
                response.success = False
                response.message = "Extraction failed"
        
        except Exception as e:
            response.success = False
            response.message = f"Extraction failed: {str(e)}"
            logger.error(f"Extraction error: {e}")
        
        finally:
            self.stats['active_jobs'] -= 1
        
        return response
    
    def ValidateSVG(self, request: ValidateSVGRequest, context) -> ValidateSVGResponse:
        """Validate SVG file and detect mp4svg format"""
        response = ValidateSVGResponse()
        
        try:
            logger.info(f"Validating SVG file: {request.file_path}")
            
            if not os.path.exists(request.file_path):
                response.is_valid = False
                response.errors = [f"File not found: {request.file_path}"]
                return response
            
            # Perform validation
            result = self.svg_validator.validate_svg_file(request.file_path)
            
            response.is_valid = result.get('is_valid', False)
            response.detected_format = result.get('detected_format', '')
            response.errors = result.get('errors', [])
            response.warnings = result.get('warnings', [])
            
            self.stats['total_validations'] += 1
            logger.info(f"SVG validation completed - valid: {response.is_valid}")
        
        except Exception as e:
            response.is_valid = False
            response.errors = [f"Validation failed: {str(e)}"]
            logger.error(f"SVG validation error: {e}")
        
        return response
    
    def ValidateIntegrity(self, request: ValidateIntegrityRequest, context) -> ValidateIntegrityResponse:
        """Validate conversion roundtrip integrity"""
        response = ValidateIntegrityResponse()
        
        try:
            logger.info(f"Validating integrity: {request.original_path} vs {request.svg_path}")
            
            # Validate inputs
            if not os.path.exists(request.original_path):
                response.integrity_valid = False
                response.message = f"Original file not found: {request.original_path}"
                return response
            
            if not os.path.exists(request.svg_path):
                response.integrity_valid = False
                response.message = f"SVG file not found: {request.svg_path}"
                return response
            
            # Perform integrity validation
            result = self.integrity_validator.validate_integrity(
                request.original_path, request.svg_path, request.method
            )
            
            response.integrity_valid = result.get('integrity_valid', False)
            response.message = result.get('message', '')
            response.similarity_score = result.get('similarity_score', 0.0)
            
            logger.info(f"Integrity validation completed - valid: {response.integrity_valid}")
        
        except Exception as e:
            response.integrity_valid = False
            response.message = f"Integrity validation failed: {str(e)}"
            logger.error(f"Integrity validation error: {e}")
        
        return response
    
    def ListConverters(self, request: ListConvertersRequest, context) -> ListConvertersResponse:
        """List all available conversion methods"""
        response = ListConvertersResponse()
        
        try:
            converter_list = list_converters()
            response.total_count = len(converter_list)
            
            for name in converter_list:
                converter_info = ConverterInfo()
                converter_info.name = name
                converter_info.description = (
                    self.converters[name].__doc__ or f"{name.upper()} converter"
                )
                converter_info.supported_operations = ["convert"]
                if name in ["ascii85", "polyglot"]:
                    converter_info.supported_operations.append("extract")
                converter_info.supports_streaming = (name in ["vector", "qrcode"])
                
                response.converters.append(converter_info)
            
            logger.info(f"Listed {response.total_count} converters")
        
        except Exception as e:
            logger.error(f"List converters error: {e}")
        
        return response
    
    def GetServerInfo(self, request: GetServerInfoRequest, context) -> GetServerInfoResponse:
        """Get server information and statistics"""
        response = GetServerInfoResponse()
        
        try:
            uptime = time.time() - self.stats['start_time']
            
            response.server_name = "mp4svg-grpc-server"
            response.version = "1.0.1"
            response.build_time = str(int(self.stats['start_time']))
            response.supported_formats = ["MP4", "AVI", "MOV", "MKV"]
            
            # Note: In real implementation, you'd populate these with actual data
            # response.capabilities = ServerCapabilities(...)
            # response.stats = ServerStats(...)
            
            logger.info(f"Server info requested - uptime: {uptime:.1f}s")
        
        except Exception as e:
            logger.error(f"Get server info error: {e}")
        
        return response

def serve(port: int = 50051, max_workers: int = 10):
    """Start the gRPC server"""
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=max_workers))
    
    # Add the servicer to the server
    # In real implementation: add_MP4SVGServiceServicer_to_server(MP4SVGServicer(), server)
    # For now, we'll use a mock approach
    servicer = MP4SVGServicer()
    server.add_insecure_port(f"[::]:{port}")
    
    logger.info(f"Starting mp4svg gRPC server on port {port} with {max_workers} workers")
    server.start()
    
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        logger.info("Stopping server...")
        server.stop(0)

async def serve_async(port: int = 50051, max_workers: int = 10):
    """Start the async gRPC server"""
    server = grpc.aio.server()
    
    # Add the servicer to the server (async version)
    servicer = MP4SVGServicer()
    server.add_insecure_port(f"[::]:{port}")
    
    logger.info(f"Starting async mp4svg gRPC server on port {port}")
    await server.start()
    
    try:
        await server.wait_for_termination()
    except KeyboardInterrupt:
        logger.info("Stopping async server...")
        await server.stop(0)

def main():
    """Main entry point for gRPC server"""
    import argparse
    
    parser = argparse.ArgumentParser(description="MP4SVG gRPC Server")
    parser.add_argument("--port", type=int, default=50051, help="Server port")
    parser.add_argument("--max-workers", type=int, default=10, help="Maximum worker threads")
    parser.add_argument("--async", action="store_true", help="Use async server")
    
    args = parser.parse_args()
    
    if args.async:
        asyncio.run(serve_async(args.port, args.max_workers))
    else:
        serve(args.port, args.max_workers)

if __name__ == "__main__":
    main()
