"""
REST API Server for mp4svg
Provides HTTP endpoints for video-to-SVG conversion with OpenAPI documentation
"""

import os
import tempfile
import shutil
from pathlib import Path
from typing import Optional, Dict, Any, List
import mimetypes
from datetime import datetime
import hashlib

from fastapi import (
    FastAPI, File, UploadFile, HTTPException, BackgroundTasks,
    Depends, Query, Path as PathParam, Response
)
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
import uvicorn

from . import (
    get_converter, list_converters, CONVERTER_REGISTRY,
    EncodingError, DecodingError, ValidationError
)
from .validators import SVGValidator, IntegrityValidator


# Pydantic models for API requests/responses
class ConversionRequest(BaseModel):
    """Request model for video conversion"""
    method: str = Field(
        default="ascii85",
        description="Conversion method",
        regex="^(ascii85|polyglot|vector|qrcode|hybrid)$"
    )
    chunk_size: Optional[int] = Field(
        default=None,
        description="Chunk size for applicable methods",
        ge=100,
        le=10000
    )
    max_frames: Optional[int] = Field(
        default=None,
        description="Maximum frames for vector method",
        ge=1,
        le=1000
    )
    error_correction: Optional[str] = Field(
        default="M",
        description="QR code error correction level",
        regex="^[LMQH]$"
    )
    thumbnail_quality: Optional[int] = Field(
        default=75,
        description="JPEG thumbnail quality",
        ge=1,
        le=100
    )


class ConversionResponse(BaseModel):
    """Response model for successful conversion"""
    job_id: str = Field(description="Unique job identifier")
    method: str = Field(description="Conversion method used")
    input_filename: str = Field(description="Original filename")
    output_filename: str = Field(description="Generated SVG filename")
    file_size_mb: float = Field(description="Output file size in MB")
    processing_time_seconds: float = Field(description="Processing duration")
    download_url: str = Field(description="URL to download the SVG file")
    metadata: Dict[str, Any] = Field(description="Additional metadata")


class ValidationRequest(BaseModel):
    """Request model for SVG validation"""
    check_integrity: bool = Field(
        default=False,
        description="Whether to perform integrity validation"
    )
    original_filename: Optional[str] = Field(
        default=None,
        description="Original MP4 filename for integrity check"
    )


class ValidationResponse(BaseModel):
    """Response model for validation results"""
    is_well_formed: bool = Field(description="Whether SVG is well-formed XML")
    is_valid: bool = Field(description="Overall validation status")
    detected_format: Optional[str] = Field(description="Detected mp4svg format")
    metadata: Dict[str, Any] = Field(description="Extracted metadata")
    errors: List[str] = Field(description="Validation errors")
    warnings: List[str] = Field(description="Validation warnings")
    integrity_check: Optional[Dict[str, Any]] = Field(description="Integrity validation results")


class JobStatus(BaseModel):
    """Response model for job status"""
    job_id: str = Field(description="Job identifier")
    status: str = Field(description="Job status: pending, processing, completed, failed")
    progress: Optional[float] = Field(description="Progress percentage (0-100)")
    message: Optional[str] = Field(description="Status message")
    result: Optional[ConversionResponse] = Field(description="Result if completed")
    error: Optional[str] = Field(description="Error message if failed")


class ErrorResponse(BaseModel):
    """Response model for errors"""
    error: str = Field(description="Error type")
    message: str = Field(description="Error message")
    details: Optional[Dict[str, Any]] = Field(description="Additional error details")


# Global variables for job management
jobs_storage: Dict[str, Dict[str, Any]] = {}
temp_storage = tempfile.mkdtemp(prefix="mp4svg_api_")


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    
    app = FastAPI(
        title="MP4SVG API",
        description="""
        REST API for converting MP4 videos to SVG containers using various encoding methods.
        
        ## Features
        
        * **Multiple Encoding Methods**: ASCII85, Polyglot, Vector, QR Code, Hybrid
        * **File Upload/Download**: Support for large video files
        * **Async Processing**: Background job processing for large files  
        * **Validation**: SVG structure and data integrity validation
        * **Interactive Documentation**: Auto-generated OpenAPI docs
        
        ## Encoding Methods
        
        * **ASCII85**: Recommended for general use (25% overhead)
        * **Polyglot**: Maximum compatibility (33% overhead)
        * **Vector**: Artistic animation effects (variable size)
        * **QR Code**: Educational/distributed storage (10x size)
        * **Hybrid**: Compare all methods automatically
        """,
        version="1.0.0",
        contact={
            "name": "MP4SVG Project",
            "email": "contact@mp4svg.org",
        },
        license_info={
            "name": "MIT License",
            "url": "https://opensource.org/licenses/MIT",
        }
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Initialize converters
    converters = {}
    for name in list_converters():
        converter_class = get_converter(name)
        converters[name] = converter_class()
    
    # Initialize validators
    svg_validator = SVGValidator()
    integrity_validator = IntegrityValidator()
    
    def get_job_id() -> str:
        """Generate unique job ID"""
        return hashlib.md5(
            f"{datetime.now().isoformat()}_{os.urandom(8).hex()}".encode()
        ).hexdigest()[:16]
    
    def apply_converter_options(converter, options: ConversionRequest):
        """Apply request options to converter"""
        if options.chunk_size and hasattr(converter, 'chunk_size'):
            converter.chunk_size = options.chunk_size
        if options.max_frames and hasattr(converter, 'max_frames'):
            converter.max_frames = options.max_frames
        if options.error_correction and hasattr(converter, 'error_correction'):
            converter.error_correction = options.error_correction
        if options.thumbnail_quality and hasattr(converter, 'thumbnail_quality'):
            converter.thumbnail_quality = options.thumbnail_quality
    
    async def process_conversion_job(
        job_id: str,
        input_path: str,
        output_path: str,
        method: str,
        options: ConversionRequest,
        original_filename: str
    ):
        """Background task for processing conversion jobs"""
        try:
            jobs_storage[job_id]['status'] = 'processing'
            jobs_storage[job_id]['progress'] = 0.0
            
            start_time = datetime.now()
            
            # Get converter
            converter = converters[method]
            apply_converter_options(converter, options)
            
            jobs_storage[job_id]['progress'] = 25.0
            
            # Perform conversion
            result_path = converter.convert(input_path, output_path)
            
            jobs_storage[job_id]['progress'] = 75.0
            
            if result_path:
                end_time = datetime.now()
                processing_time = (end_time - start_time).total_seconds()
                file_size_mb = os.path.getsize(result_path) / (1024 * 1024)
                
                # Create response
                result = ConversionResponse(
                    job_id=job_id,
                    method=method,
                    input_filename=original_filename,
                    output_filename=os.path.basename(result_path),
                    file_size_mb=round(file_size_mb, 2),
                    processing_time_seconds=round(processing_time, 2),
                    download_url=f"/api/v1/download/{job_id}",
                    metadata={
                        "converter_type": method,
                        "created_at": end_time.isoformat(),
                        "original_size_mb": round(os.path.getsize(input_path) / (1024 * 1024), 2)
                    }
                )
                
                jobs_storage[job_id].update({
                    'status': 'completed',
                    'progress': 100.0,
                    'result': result,
                    'output_path': result_path
                })
            else:
                jobs_storage[job_id].update({
                    'status': 'failed',
                    'error': 'Conversion failed - no output produced'
                })
                
        except Exception as e:
            jobs_storage[job_id].update({
                'status': 'failed',
                'error': f"Conversion error: {str(e)}"
            })
        
        finally:
            # Clean up input file
            try:
                os.unlink(input_path)
            except:
                pass
    
    @app.get("/", tags=["General"])
    async def root():
        """API root endpoint with basic information"""
        return {
            "name": "MP4SVG API",
            "version": "1.0.0",
            "description": "Convert MP4 videos to SVG containers",
            "docs_url": "/docs",
            "redoc_url": "/redoc",
            "openapi_url": "/openapi.json"
        }
    
    @app.get("/api/v1/methods", tags=["Information"])
    async def get_methods():
        """Get available conversion methods and their descriptions"""
        return {
            "methods": {
                "ascii85": {
                    "name": "ASCII85",
                    "description": "Recommended for general use",
                    "overhead": "~25%",
                    "features": ["Interactive playback", "Thumbnail preview", "XML-safe"],
                    "roundtrip": True
                },
                "polyglot": {
                    "name": "Polyglot",
                    "description": "Maximum compatibility",
                    "overhead": "~33%",
                    "features": ["SVG + embedded binary", "Summary statistics"],
                    "roundtrip": True
                },
                "vector": {
                    "name": "Vector Animation",
                    "description": "Artistic animation effects",
                    "overhead": "Variable",
                    "features": ["True vector animation", "Scalable"],
                    "roundtrip": False
                },
                "qrcode": {
                    "name": "QR Code",
                    "description": "Educational/distributed storage",
                    "overhead": "~1000%",
                    "features": ["Multiple QR frames", "Chunk-based storage"],
                    "roundtrip": True
                },
                "hybrid": {
                    "name": "Hybrid",
                    "description": "Compare all methods",
                    "overhead": "N/A",
                    "features": ["Size comparison", "Format detection"],
                    "roundtrip": "Method-dependent"
                }
            }
        }
    
    @app.post(
        "/api/v1/convert",
        response_model=ConversionResponse,
        tags=["Conversion"],
        responses={
            202: {"description": "Conversion started (async processing)"},
            400: {"model": ErrorResponse, "description": "Invalid request"},
            413: {"description": "File too large"},
            422: {"description": "Validation error"}
        }
    )
    async def convert_video(
        background_tasks: BackgroundTasks,
        file: UploadFile = File(..., description="MP4 video file to convert"),
        method: str = Query(
            default="ascii85",
            description="Conversion method",
            regex="^(ascii85|polyglot|vector|qrcode|hybrid)$"
        ),
        chunk_size: Optional[int] = Query(default=None, description="Chunk size for applicable methods"),
        max_frames: Optional[int] = Query(default=None, description="Maximum frames for vector method"),
        error_correction: str = Query(default="M", description="QR code error correction level"),
        thumbnail_quality: int = Query(default=75, description="JPEG thumbnail quality"),
        async_processing: bool = Query(default=False, description="Process asynchronously for large files")
    ):
        """Convert MP4 video to SVG using specified method"""
        
        # Validate file type
        if not file.filename.lower().endswith('.mp4'):
            raise HTTPException(
                status_code=400,
                detail={"error": "invalid_file_type", "message": "Only MP4 files are supported"}
            )
        
        # Check file size (100MB limit)
        max_size = 100 * 1024 * 1024  # 100MB
        content = await file.read()
        if len(content) > max_size:
            raise HTTPException(
                status_code=413,
                detail={"error": "file_too_large", "message": f"File size exceeds {max_size // (1024*1024)}MB limit"}
            )
        
        # Create temporary input file
        job_id = get_job_id()
        input_path = os.path.join(temp_storage, f"{job_id}_input.mp4")
        output_path = os.path.join(temp_storage, f"{job_id}_output.svg")
        
        with open(input_path, 'wb') as f:
            f.write(content)
        
        # Create conversion options
        options = ConversionRequest(
            method=method,
            chunk_size=chunk_size,
            max_frames=max_frames,
            error_correction=error_correction,
            thumbnail_quality=thumbnail_quality
        )
        
        # Initialize job
        jobs_storage[job_id] = {
            'job_id': job_id,
            'status': 'pending',
            'progress': 0.0,
            'method': method,
            'original_filename': file.filename,
            'created_at': datetime.now().isoformat()
        }
        
        if async_processing or len(content) > 10 * 1024 * 1024:  # 10MB threshold
            # Process asynchronously
            background_tasks.add_task(
                process_conversion_job,
                job_id, input_path, output_path, method, options, file.filename
            )
            
            return JSONResponse(
                status_code=202,
                content={
                    "job_id": job_id,
                    "status": "accepted",
                    "message": "Conversion started in background",
                    "status_url": f"/api/v1/jobs/{job_id}"
                }
            )
        else:
            # Process synchronously
            try:
                start_time = datetime.now()
                
                converter = converters[method]
                apply_converter_options(converter, options)
                
                result_path = converter.convert(input_path, output_path)
                
                if result_path:
                    end_time = datetime.now()
                    processing_time = (end_time - start_time).total_seconds()
                    file_size_mb = os.path.getsize(result_path) / (1024 * 1024)
                    
                    # Store job result
                    result = ConversionResponse(
                        job_id=job_id,
                        method=method,
                        input_filename=file.filename,
                        output_filename=os.path.basename(result_path),
                        file_size_mb=round(file_size_mb, 2),
                        processing_time_seconds=round(processing_time, 2),
                        download_url=f"/api/v1/download/{job_id}",
                        metadata={
                            "converter_type": method,
                            "created_at": end_time.isoformat(),
                            "original_size_mb": round(len(content) / (1024 * 1024), 2)
                        }
                    )
                    
                    jobs_storage[job_id].update({
                        'status': 'completed',
                        'result': result,
                        'output_path': result_path
                    })
                    
                    return result
                else:
                    raise HTTPException(
                        status_code=500,
                        detail={"error": "conversion_failed", "message": "Conversion failed - no output produced"}
                    )
                    
            except (EncodingError, DecodingError) as e:
                raise HTTPException(
                    status_code=400,
                    detail={"error": "encoding_error", "message": str(e)}
                )
            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail={"error": "internal_error", "message": f"Conversion error: {str(e)}"}
                )
            finally:
                # Clean up input file
                try:
                    os.unlink(input_path)
                except:
                    pass
    
    @app.get(
        "/api/v1/jobs/{job_id}",
        response_model=JobStatus,
        tags=["Jobs"],
        responses={404: {"model": ErrorResponse, "description": "Job not found"}}
    )
    async def get_job_status(job_id: str = PathParam(..., description="Job ID")):
        """Get status of a conversion job"""
        
        if job_id not in jobs_storage:
            raise HTTPException(
                status_code=404,
                detail={"error": "job_not_found", "message": f"Job {job_id} not found"}
            )
        
        job_data = jobs_storage[job_id]
        
        return JobStatus(
            job_id=job_id,
            status=job_data['status'],
            progress=job_data.get('progress'),
            message=job_data.get('message'),
            result=job_data.get('result'),
            error=job_data.get('error')
        )
    
    @app.get(
        "/api/v1/download/{job_id}",
        tags=["Download"],
        responses={
            200: {"description": "SVG file download"},
            404: {"model": ErrorResponse, "description": "File not found"}
        }
    )
    async def download_result(job_id: str = PathParam(..., description="Job ID")):
        """Download the converted SVG file"""
        
        if job_id not in jobs_storage:
            raise HTTPException(
                status_code=404,
                detail={"error": "job_not_found", "message": f"Job {job_id} not found"}
            )
        
        job_data = jobs_storage[job_id]
        
        if job_data['status'] != 'completed':
            raise HTTPException(
                status_code=400,
                detail={"error": "job_not_completed", "message": f"Job {job_id} is not completed"}
            )
        
        output_path = job_data.get('output_path')
        
        if not output_path or not os.path.exists(output_path):
            raise HTTPException(
                status_code=404,
                detail={"error": "file_not_found", "message": "Output file not found"}
            )
        
        filename = job_data.get('result', {}).get('output_filename', 'output.svg')
        
        return FileResponse(
            path=output_path,
            filename=filename,
            media_type='image/svg+xml'
        )
    
    @app.post(
        "/api/v1/validate",
        response_model=ValidationResponse,
        tags=["Validation"],
        responses={400: {"model": ErrorResponse, "description": "Invalid request"}}
    )
    async def validate_svg(
        file: UploadFile = File(..., description="SVG file to validate"),
        check_integrity: bool = Query(default=False, description="Perform integrity validation"),
        original_file: Optional[UploadFile] = File(None, description="Original MP4 file for integrity check")
    ):
        """Validate SVG file structure and optionally check data integrity"""
        
        # Validate file type
        if not file.filename.lower().endswith('.svg'):
            raise HTTPException(
                status_code=400,
                detail={"error": "invalid_file_type", "message": "Only SVG files are supported for validation"}
            )
        
        # Save SVG file temporarily
        svg_content = await file.read()
        svg_path = os.path.join(temp_storage, f"validate_{get_job_id()}.svg")
        
        with open(svg_path, 'wb') as f:
            f.write(svg_content)
        
        try:
            # SVG validation
            svg_result = svg_validator.validate_svg_file(svg_path)
            
            response_data = {
                "is_well_formed": svg_result['is_well_formed'],
                "is_valid": svg_result['is_valid'],
                "detected_format": svg_result.get('detected_format'),
                "metadata": svg_result.get('metadata', {}),
                "errors": svg_result.get('errors', []),
                "warnings": svg_result.get('warnings', []),
                "integrity_check": None
            }
            
            # Integrity validation if requested
            if check_integrity:
                original_path = None
                if original_file:
                    original_content = await original_file.read()
                    original_path = os.path.join(temp_storage, f"validate_{get_job_id()}.mp4")
                    with open(original_path, 'wb') as f:
                        f.write(original_content)
                
                integrity_result = integrity_validator.validate_integrity(svg_path, original_path)
                response_data["integrity_check"] = integrity_result
                
                # Clean up original file
                if original_path:
                    try:
                        os.unlink(original_path)
                    except:
                        pass
            
            return ValidationResponse(**response_data)
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail={"error": "validation_error", "message": f"Validation failed: {str(e)}"}
            )
        finally:
            # Clean up SVG file
            try:
                os.unlink(svg_path)
            except:
                pass
    
    @app.delete(
        "/api/v1/jobs/{job_id}",
        tags=["Jobs"],
        responses={204: {"description": "Job deleted successfully"}}
    )
    async def delete_job(job_id: str = PathParam(..., description="Job ID")):
        """Delete a job and clean up associated files"""
        
        if job_id in jobs_storage:
            job_data = jobs_storage[job_id]
            
            # Clean up output file
            output_path = job_data.get('output_path')
            if output_path and os.path.exists(output_path):
                try:
                    os.unlink(output_path)
                except:
                    pass
            
            # Remove from storage
            del jobs_storage[job_id]
        
        return Response(status_code=204)
    
    @app.get("/api/v1/health", tags=["General"])
    async def health_check():
        """Health check endpoint"""
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "active_jobs": len([j for j in jobs_storage.values() if j['status'] == 'processing']),
            "total_jobs": len(jobs_storage),
            "temp_storage": temp_storage
        }
    
    return app


def main():
    """Run the API server"""
    app = create_app()
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True,
        access_log=True
    )


if __name__ == "__main__":
    main()
