"""
MCP (Model Context Protocol) Client for mp4svg
Client interface for connecting to and using mp4svg MCP servers
"""

import asyncio
import json
import logging
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

import mcp
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MP4SVGMCPClient:
    """MCP Client for mp4svg video conversion services"""
    
    def __init__(self, server_path: Optional[str] = None):
        """Initialize MCP client
        
        Args:
            server_path: Path to mp4svg MCP server script (auto-detected if None)
        """
        self.server_path = server_path or self._find_server_path()
        self.session = None
        
    def _find_server_path(self) -> str:
        """Auto-detect the mp4svg MCP server path"""
        # Try to find the server script in common locations
        possible_paths = [
            "mp4svg-mcp",  # If installed as command
            sys.executable + " -m mp4svg.mcp_server",  # As module
            Path(__file__).parent / "mcp_server.py",  # In same directory
        ]
        
        for path in possible_paths:
            try:
                if isinstance(path, Path) and path.exists():
                    return f"{sys.executable} {path}"
                elif isinstance(path, str) and path.startswith("mp4svg-mcp"):
                    # Check if command exists
                    result = subprocess.run(["which", "mp4svg-mcp"], 
                                          capture_output=True, text=True)
                    if result.returncode == 0:
                        return path
                elif isinstance(path, str) and "python" in path:
                    return path
            except Exception:
                continue
                
        # Default fallback
        return f"{sys.executable} -m mp4svg.mcp_server"
    
    async def connect(self):
        """Connect to the MCP server"""
        server_params = StdioServerParameters(
            command=self.server_path.split(),
            env=None
        )
        
        self.stdio_client = stdio_client(server_params)
        self.read_stream, self.write_stream, _ = await self.stdio_client.__aenter__()
        self.session = await ClientSession(self.read_stream, self.write_stream).__aenter__()
        
        # Initialize the session
        await self.session.initialize()
        logger.info("Connected to mp4svg MCP server")
    
    async def disconnect(self):
        """Disconnect from the MCP server"""
        if self.session:
            await self.session.__aexit__(None, None, None)
        if hasattr(self, 'stdio_client'):
            await self.stdio_client.__aexit__(None, None, None)
        logger.info("Disconnected from mp4svg MCP server")
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """List all available tools on the server"""
        if not self.session:
            raise RuntimeError("Not connected to server")
            
        tools = await self.session.list_tools()
        return [tool.model_dump() for tool in tools.tools]
    
    async def list_resources(self) -> List[Dict[str, Any]]:
        """List all available resources on the server"""
        if not self.session:
            raise RuntimeError("Not connected to server")
            
        resources = await self.session.list_resources()
        return [resource.model_dump() for resource in resources.resources]
    
    async def convert_video(self, input_path: str, output_path: str, 
                          method: str, options: Optional[Dict] = None) -> Dict[str, Any]:
        """Convert MP4 video to SVG using specified method
        
        Args:
            input_path: Path to input MP4 file
            output_path: Path for output SVG file
            method: Conversion method (ascii85, polyglot, vector, qrcode, hybrid)
            options: Method-specific options
            
        Returns:
            Conversion result dictionary
        """
        if not self.session:
            raise RuntimeError("Not connected to server")
        
        args = {
            "input_path": input_path,
            "output_path": output_path,
            "method": method
        }
        if options:
            args["options"] = options
            
        result = await self.session.call_tool("convert_video", args)
        return json.loads(result.content[0].text)
    
    async def extract_video(self, input_path: str, output_path: str, 
                          method: Optional[str] = None) -> Dict[str, Any]:
        """Extract MP4 video from SVG file
        
        Args:
            input_path: Path to input SVG file
            output_path: Path for extracted MP4 file
            method: Extraction method (auto-detect if None)
            
        Returns:
            Extraction result dictionary
        """
        if not self.session:
            raise RuntimeError("Not connected to server")
        
        args = {
            "input_path": input_path,
            "output_path": output_path
        }
        if method:
            args["method"] = method
            
        result = await self.session.call_tool("extract_video", args)
        return json.loads(result.content[0].text)
    
    async def validate_svg(self, file_path: str) -> Dict[str, Any]:
        """Validate SVG file and detect mp4svg format
        
        Args:
            file_path: Path to SVG file to validate
            
        Returns:
            Validation result dictionary
        """
        if not self.session:
            raise RuntimeError("Not connected to server")
        
        args = {"file_path": file_path}
        result = await self.session.call_tool("validate_svg", args)
        return json.loads(result.content[0].text)
    
    async def validate_integrity(self, original_path: str, svg_path: str, 
                               method: str) -> Dict[str, Any]:
        """Validate conversion roundtrip integrity
        
        Args:
            original_path: Path to original MP4 file
            svg_path: Path to converted SVG file
            method: Conversion method used
            
        Returns:
            Integrity validation result dictionary
        """
        if not self.session:
            raise RuntimeError("Not connected to server")
        
        args = {
            "original_path": original_path,
            "svg_path": svg_path,
            "method": method
        }
        result = await self.session.call_tool("validate_integrity", args)
        return json.loads(result.content[0].text)
    
    async def list_converters(self) -> Dict[str, Any]:
        """List all available conversion methods
        
        Returns:
            Dictionary with converter information
        """
        if not self.session:
            raise RuntimeError("Not connected to server")
        
        result = await self.session.call_tool("list_converters", {})
        return json.loads(result.content[0].text)
    
    async def read_resource(self, uri: str) -> Dict[str, Any]:
        """Read resource information
        
        Args:
            uri: Resource URI (e.g., "converter://ascii85")
            
        Returns:
            Resource information dictionary
        """
        if not self.session:
            raise RuntimeError("Not connected to server")
        
        resource = await self.session.read_resource(uri)
        return json.loads(resource.contents[0].text)

class MP4SVGMCPClientCLI:
    """Command-line interface for MCP client"""
    
    def __init__(self):
        self.client = MP4SVGMCPClient()
    
    async def run_interactive(self):
        """Run interactive MCP client session"""
        print("🚀 MP4SVG MCP Client - Interactive Mode")
        print("Connecting to server...")
        
        try:
            await self.client.connect()
            print("✅ Connected to mp4svg MCP server\n")
            
            # Show available tools
            tools = await self.client.list_tools()
            print(f"📋 Available tools: {len(tools)}")
            for tool in tools:
                print(f"  - {tool['name']}: {tool['description']}")
            print()
            
            # Interactive loop
            while True:
                try:
                    command = input("mcp> ").strip()
                    if not command:
                        continue
                    
                    if command in ["exit", "quit", "q"]:
                        break
                    elif command == "help":
                        self.show_help()
                    elif command == "tools":
                        await self.show_tools()
                    elif command == "resources":
                        await self.show_resources()
                    elif command == "converters":
                        await self.show_converters()
                    elif command.startswith("convert "):
                        await self.handle_convert(command)
                    elif command.startswith("extract "):
                        await self.handle_extract(command)
                    elif command.startswith("validate "):
                        await self.handle_validate(command)
                    else:
                        print("Unknown command. Type 'help' for available commands.")
                        
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    print(f"❌ Error: {e}")
            
        except Exception as e:
            print(f"❌ Failed to connect: {e}")
        finally:
            await self.client.disconnect()
            print("👋 Disconnected from server")
    
    def show_help(self):
        """Show help information"""
        print("""
📖 Available commands:
  help                    - Show this help
  tools                   - List available tools
  resources              - List available resources
  converters             - List available converters
  convert <args>         - Convert video (format: input.mp4 output.svg method [options])
  extract <args>         - Extract video (format: input.svg output.mp4 [method])
  validate <file>        - Validate SVG file
  exit/quit/q           - Exit client
        """)
    
    async def show_tools(self):
        """Show available tools"""
        tools = await self.client.list_tools()
        print(f"📋 Available tools ({len(tools)}):")
        for tool in tools:
            print(f"  🔧 {tool['name']}")
            print(f"     {tool['description']}")
            if 'inputSchema' in tool:
                required = tool['inputSchema'].get('required', [])
                if required:
                    print(f"     Required: {', '.join(required)}")
            print()
    
    async def show_resources(self):
        """Show available resources"""
        resources = await self.client.list_resources()
        print(f"📚 Available resources ({len(resources)}):")
        for resource in resources:
            print(f"  📄 {resource['name']}")
            print(f"     URI: {resource['uri']}")
            print(f"     {resource['description']}")
            print()
    
    async def show_converters(self):
        """Show available converters"""
        result = await self.client.list_converters()
        print(f"🔄 Available converters ({result['count']}):")
        for name, desc in result['descriptions'].items():
            print(f"  • {name}: {desc}")
        print()
    
    async def handle_convert(self, command: str):
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
                    # Try to convert to int or float
                    if '.' in value:
                        options[key] = float(value)
                    else:
                        options[key] = int(value)
                except ValueError:
                    options[key] = value
        
        print(f"🔄 Converting {input_path} → {output_path} using {method}...")
        result = await self.client.convert_video(input_path, output_path, method, options)
        
        if result.get("status") == "success":
            print(f"✅ Conversion successful!")
            print(f"   Input size: {result['input_size_bytes']:,} bytes")
            print(f"   Output size: {result['output_size_bytes']:,} bytes")
            print(f"   Compression ratio: {result['compression_ratio']}")
        else:
            print(f"❌ Conversion failed: {result}")
    
    async def handle_extract(self, command: str):
        """Handle extract command"""
        parts = command.split()[1:]  # Remove 'extract'
        if len(parts) < 2:
            print("Usage: extract <input.svg> <output.mp4> [method]")
            return
        
        input_path, output_path = parts[:2]
        method = parts[2] if len(parts) > 2 else None
        
        print(f"📤 Extracting {input_path} → {output_path}...")
        result = await self.client.extract_video(input_path, output_path, method)
        
        if result.get("status") == "success":
            print(f"✅ Extraction successful!")
            print(f"   Method: {result['method']}")
            print(f"   Output size: {result['output_size_bytes']:,} bytes")
        else:
            print(f"❌ Extraction failed: {result}")
    
    async def handle_validate(self, command: str):
        """Handle validate command"""
        parts = command.split()[1:]  # Remove 'validate'
        if len(parts) < 1:
            print("Usage: validate <file.svg>")
            return
        
        file_path = parts[0]
        print(f"🔍 Validating {file_path}...")
        result = await self.client.validate_svg(file_path)
        
        print(f"📊 Validation results:")
        print(f"   Valid: {result['is_valid']}")
        print(f"   Format: {result.get('detected_format', 'Unknown')}")
        if result.get('errors'):
            print(f"   Errors: {len(result['errors'])}")
        if result.get('warnings'):
            print(f"   Warnings: {len(result['warnings'])}")

async def main():
    """Main entry point for MCP client CLI"""
    import argparse
    
    parser = argparse.ArgumentParser(description="MP4SVG MCP Client")
    parser.add_argument("--server-path", help="Path to MCP server script")
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
    
    args = parser.parse_args()
    
    client_cli = MP4SVGMCPClientCLI()
    if args.server_path:
        client_cli.client.server_path = args.server_path
    
    if args.interactive:
        await client_cli.run_interactive()
    else:
        # Handle individual commands
        await client_cli.client.connect()
        
        try:
            if args.convert:
                input_path, output_path, method = args.convert
                result = await client_cli.client.convert_video(input_path, output_path, method)
                print(json.dumps(result, indent=2))
            
            elif args.extract:
                input_path, output_path = args.extract
                result = await client_cli.client.extract_video(input_path, output_path)
                print(json.dumps(result, indent=2))
            
            elif args.validate:
                result = await client_cli.client.validate_svg(args.validate)
                print(json.dumps(result, indent=2))
            
            elif args.list_converters:
                result = await client_cli.client.list_converters()
                print(json.dumps(result, indent=2))
            
            else:
                parser.print_help()
        
        finally:
            await client_cli.client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
