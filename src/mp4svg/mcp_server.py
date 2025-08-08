"""
MCP (Model Context Protocol) Server for mp4svg
Provides video conversion and SVG validation services over MCP protocol
"""

import asyncio
import json
import logging
import os
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional

from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
import mcp.server.stdio
import mcp.types as types

from . import get_converter, list_converters, CONVERTER_REGISTRY
from .validators import SVGValidator, IntegrityValidator
from .base import EncodingError, DecodingError, ValidationError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize converters and validators
converters = {}
for name in list_converters():
    converter_class = get_converter(name)
    converters[name] = converter_class()

svg_validator = SVGValidator()
integrity_validator = IntegrityValidator()

# Create MCP server instance
server = Server("mp4svg")

@server.list_resources()
async def handle_list_resources() -> list[types.Resource]:
    """List available conversion methods and validation tools"""
    resources = []
    
    # Add converter resources
    for name in list_converters():
        resources.append(
            types.Resource(
                uri=f"converter://{name}",
                name=f"MP4SVG {name.upper()} Converter",
                description=f"Convert MP4 videos to SVG using {name} encoding method",
                mimeType="application/json"
            )
        )
    
    # Add validator resources
    resources.extend([
        types.Resource(
            uri="validator://svg",
            name="SVG Validator",
            description="Validate SVG files for compliance and detect mp4svg formats",
            mimeType="application/json"
        ),
        types.Resource(
            uri="validator://integrity",
            name="Integrity Validator", 
            description="Validate roundtrip conversion integrity",
            mimeType="application/json"
        )
    ])
    
    return resources

@server.read_resource()
async def handle_read_resource(uri: types.AnyUrl) -> str:
    """Read resource information"""
    uri_str = str(uri)
    
    if uri_str.startswith("converter://"):
        method = uri_str.replace("converter://", "")
        if method in converters:
            converter = converters[method]
            return json.dumps({
                "type": "converter",
                "method": method,
                "description": converter.__doc__ or f"{method.upper()} converter",
                "supported_operations": ["convert", "extract"]
            })
    
    elif uri_str.startswith("validator://"):
        validator_type = uri_str.replace("validator://", "")
        if validator_type == "svg":
            return json.dumps({
                "type": "validator",
                "name": "SVG Validator",
                "description": "Validates SVG files and detects mp4svg formats",
                "supported_formats": ["ascii85", "polyglot", "vector", "qrcode", "hybrid"]
            })
        elif validator_type == "integrity":
            return json.dumps({
                "type": "validator", 
                "name": "Integrity Validator",
                "description": "Validates conversion roundtrip integrity",
                "supported_methods": ["ascii85", "polyglot"]
            })
    
    raise ValueError(f"Unknown resource: {uri}")

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available conversion and validation tools"""
    tools = [
        types.Tool(
            name="convert_video",
            description="Convert MP4 video to SVG using specified method",
            inputSchema={
                "type": "object",
                "properties": {
                    "input_path": {
                        "type": "string",
                        "description": "Path to input MP4 file"
                    },
                    "output_path": {
                        "type": "string", 
                        "description": "Path for output SVG file"
                    },
                    "method": {
                        "type": "string",
                        "enum": list_converters(),
                        "description": "Conversion method to use"
                    },
                    "options": {
                        "type": "object",
                        "description": "Method-specific options",
                        "properties": {
                            "chunk_size": {"type": "integer", "description": "Chunk size for QR method"},
                            "max_frames": {"type": "integer", "description": "Max frames for vector method"},
                            "edge_threshold": {"type": "number", "description": "Edge threshold for vector method"}
                        }
                    }
                },
                "required": ["input_path", "output_path", "method"]
            }
        ),
        types.Tool(
            name="extract_video",
            description="Extract MP4 video from SVG file",
            inputSchema={
                "type": "object",
                "properties": {
                    "input_path": {
                        "type": "string",
                        "description": "Path to input SVG file"
                    },
                    "output_path": {
                        "type": "string",
                        "description": "Path for extracted MP4 file"
                    },
                    "method": {
                        "type": "string",
                        "enum": ["ascii85", "polyglot"],
                        "description": "Extraction method (auto-detect if not specified)"
                    }
                },
                "required": ["input_path", "output_path"]
            }
        ),
        types.Tool(
            name="validate_svg",
            description="Validate SVG file and detect mp4svg format",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to SVG file to validate"
                    }
                },
                "required": ["file_path"]
            }
        ),
        types.Tool(
            name="validate_integrity",
            description="Validate conversion roundtrip integrity",
            inputSchema={
                "type": "object",
                "properties": {
                    "original_path": {
                        "type": "string",
                        "description": "Path to original MP4 file"
                    },
                    "svg_path": {
                        "type": "string",
                        "description": "Path to converted SVG file"
                    },
                    "method": {
                        "type": "string",
                        "enum": ["ascii85", "polyglot"],
                        "description": "Conversion method used"
                    }
                },
                "required": ["original_path", "svg_path", "method"]
            }
        ),
        types.Tool(
            name="list_converters",
            description="List all available conversion methods",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]
    
    return tools

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    """Handle tool execution"""
    try:
        if name == "convert_video":
            return await convert_video_tool(arguments)
        elif name == "extract_video":
            return await extract_video_tool(arguments)
        elif name == "validate_svg":
            return await validate_svg_tool(arguments)
        elif name == "validate_integrity":
            return await validate_integrity_tool(arguments)
        elif name == "list_converters":
            return await list_converters_tool(arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")
    
    except Exception as e:
        logger.error(f"Tool execution failed: {e}")
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]

async def convert_video_tool(args: dict) -> list[types.TextContent]:
    """Convert MP4 video to SVG"""
    input_path = args["input_path"]
    output_path = args["output_path"] 
    method = args["method"]
    options = args.get("options", {})
    
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    if method not in converters:
        raise ValueError(f"Unknown conversion method: {method}")
    
    # Get converter instance
    if method == "qrcode" and "chunk_size" in options:
        converter_class = get_converter(method)
        converter = converter_class(chunk_size=options["chunk_size"])
    else:
        converter = converters[method]
    
    # Perform conversion
    if method == "vector":
        max_frames = options.get("max_frames", 30)
        edge_threshold = options.get("edge_threshold", 50)
        result_path = converter.convert(input_path, output_path, max_frames, edge_threshold)
    elif method == "polyglot":
        pdf = options.get("pdf", False)
        result_path = converter.convert(input_path, output_path, pdf)
    else:
        result_path = converter.convert(input_path, output_path)
    
    # Get file size info
    input_size = os.path.getsize(input_path)
    output_size = os.path.getsize(result_path)
    
    result = {
        "status": "success",
        "method": method,
        "input_path": input_path,
        "output_path": result_path,
        "input_size_bytes": input_size,
        "output_size_bytes": output_size,
        "compression_ratio": round(output_size / input_size, 2)
    }
    
    return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

async def extract_video_tool(args: dict) -> list[types.TextContent]:
    """Extract MP4 video from SVG"""
    input_path = args["input_path"]
    output_path = args["output_path"]
    method = args.get("method")
    
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    # Auto-detect method if not specified
    if not method:
        svg_result = svg_validator.validate_svg_file(input_path)
        method = svg_result.get("detected_format")
        if not method:
            raise ValueError("Could not auto-detect SVG format")
    
    if method not in ["ascii85", "polyglot"]:
        raise ValueError(f"Extraction not supported for method: {method}")
    
    converter = converters[method]
    success = converter.extract(input_path, output_path)
    
    if success and os.path.exists(output_path):
        output_size = os.path.getsize(output_path)
        result = {
            "status": "success",
            "method": method,
            "input_path": input_path,
            "output_path": output_path,
            "output_size_bytes": output_size
        }
    else:
        result = {
            "status": "failed",
            "method": method,
            "input_path": input_path,
            "error": "Extraction failed"
        }
    
    return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

async def validate_svg_tool(args: dict) -> list[types.TextContent]:
    """Validate SVG file"""
    file_path = args["file_path"]
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    result = svg_validator.validate_svg_file(file_path)
    return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

async def validate_integrity_tool(args: dict) -> list[types.TextContent]:
    """Validate conversion integrity"""
    original_path = args["original_path"]
    svg_path = args["svg_path"] 
    method = args["method"]
    
    if not os.path.exists(original_path):
        raise FileNotFoundError(f"Original file not found: {original_path}")
    
    if not os.path.exists(svg_path):
        raise FileNotFoundError(f"SVG file not found: {svg_path}")
    
    result = integrity_validator.validate_integrity(original_path, svg_path, method)
    return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

async def list_converters_tool(args: dict) -> list[types.TextContent]:
    """List available converters"""
    converter_list = list_converters()
    result = {
        "converters": converter_list,
        "count": len(converter_list),
        "descriptions": {
            name: converters[name].__doc__ or f"{name.upper()} converter"
            for name in converter_list
        }
    }
    return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

async def run_server():
    """Run the MCP server"""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="mp4svg",
                server_version="1.0.1",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

def main():
    """Main entry point for MCP server"""
    asyncio.run(run_server())

if __name__ == "__main__":
    main()
