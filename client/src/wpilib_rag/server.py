"""MCP server for WPILib RAG system."""

import asyncio
import io
import logging
import os
import sys
from contextlib import contextmanager
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from dotenv import load_dotenv

load_dotenv()

# Import config with error handling - server should start even if config fails
try:
    from .config import SUPPORTED_LANGUAGES, DEFAULT_VERSION
except Exception as e:
    # Fallback values if config import fails
    logger = logging.getLogger(__name__)
    logger.error(f"Failed to import config: {e}")
    SUPPORTED_LANGUAGES = ["Java", "Python", "C++", "cpp", "API Reference"]
    DEFAULT_VERSION = "2025"

# Configure logging to stderr ONLY (won't interfere with JSON-RPC on stdout)
logging.basicConfig(
    level=logging.ERROR,
    format='%(levelname)s: %(message)s',
    stream=sys.stderr,
    force=True,
)
logger = logging.getLogger(__name__)

# Suppress ALL logging from third-party libraries
for lib in ['chromadb', 'voyageai', 'httpx']:
    logging.getLogger(lib).setLevel(logging.CRITICAL)
    logging.getLogger(lib).propagate = False


@contextmanager
def suppress_stdout():
    """Context manager to suppress stdout output."""
    old_stdout = sys.stdout
    try:
        sys.stdout = io.StringIO()
        yield
    finally:
        sys.stdout = old_stdout


# Lazy import to prevent stdout pollution during module load
WPILibQueryEngine = None


# Initialize query engine
query_engine = None


def get_query_engine():
    """Get or initialize query engine."""
    global query_engine, WPILibQueryEngine
    if query_engine is None:
        # Lazy import to prevent stdout pollution
        if WPILibQueryEngine is None:
            with suppress_stdout():
                from .query_engine import WPILibQueryEngine as _WPILibQueryEngine
                WPILibQueryEngine = _WPILibQueryEngine
        
        # Initialize with stdout suppressed
        with suppress_stdout():
            try:
                query_engine = WPILibQueryEngine()
            except Exception as e:
                # Check if it's a database not found error - fail early
                from .config import DatabaseNotFoundError
                if isinstance(e, DatabaseNotFoundError):
                    logger.critical(f"Database not found: {e}")
                    logger.critical("MCP server cannot start without a valid database.")
                    sys.exit(1)
                # Re-raise other exceptions
                raise
    return query_engine


# Create MCP server with error handling
try:
    server = Server("wpilib-rag")
except Exception as e:
    logger.critical(f"Failed to create MCP server: {e}", exc_info=True)
    sys.exit(1)


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    try:
        engine = get_query_engine()
        available_versions = engine.get_available_versions()
    except Exception as e:
        # Check if it's a database not found error - fail early
        from .config import DatabaseNotFoundError
        if isinstance(e, DatabaseNotFoundError):
            logger.critical(f"Database not found: {e}")
            logger.critical("MCP server cannot start without a valid database.")
            sys.exit(1)
        
        # Ensure error message is a safe string
        error_msg = str(e) if e else "Unknown error"
        logger.error(f"Error listing tools: {error_msg}")
        # If initialization fails, return tools with default/empty versions
        # This allows the server to start even if the database is empty or API keys are missing
        available_versions = []
    
    try:
        # Safely format description strings
        versions_str = ', '.join(available_versions[:5]) if available_versions else 'None'
        
        # Build version property - only include enum if we have versions
        version_property = {
            "type": "string",
            "description": f"WPILib version (e.g., '2025', '2024'). Available versions: {versions_str}",
        }
        # Only add enum if we have available versions (JSON schema requires array, not None)
        if available_versions:
            version_property["enum"] = available_versions
        
        return [
            Tool(
                name="query_wpilib_docs",
                description=(
                    "Retrieve relevant WPILib documentation chunks for the specified version and language. "
                    "Returns formatted documentation chunks with citations that you can use to answer questions. "
                    "This tool performs retrieval only - you generate the answer from the retrieved chunks. "
                    f"If unsure, use version '{DEFAULT_VERSION}'."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "question": {
                            "type": "string",
                            "description": "The user's question about WPILib",
                        },
                        "version": version_property,
                        "language": {
                            "type": "string",
                            "description": "Programming language or documentation type",
                            "enum": SUPPORTED_LANGUAGES,
                        },
                    },
                    "required": ["question", "version", "language"],
                },
            ),
            Tool(
                name="get_latest_version",
                description=f"Return the latest WPILib version (defaults to '{DEFAULT_VERSION}' if database empty)",
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
            ),
            Tool(
                name="list_available_versions",
                description="List all available WPILib versions in the database",
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
            ),
            Tool(
                name="list_available_languages",
                description="List available languages for a specific version (or all languages)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "version": {
                            "type": "string",
                            "description": "WPILib version (optional). If not provided, returns all languages.",
                        },
                    },
                },
            ),
            Tool(
                name="embed_query",
                description=(
                    "Generate embedding vector for a query using Voyage AI. "
                    "Returns the embedding vector that can be used for client-side processing. "
                    "This is useful for caching embeddings or performing client-side similarity searches."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The text query to embed",
                        },
                    },
                    "required": ["query"],
                },
            ),
        ]
    except Exception as e:
        # Ensure error message is a safe string
        error_msg = str(e) if e else "Unknown error"
        logger.error(f"Error constructing tool list: {error_msg}")
        # Return minimal tool list if there's an error
        return [
            Tool(
                name="query_wpilib_docs",
                description="Query WPILib documentation",
                inputSchema={"type": "object", "properties": {}},
            ),
        ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any] | None) -> list[TextContent]:
    """Handle tool calls."""
    try:
        engine = get_query_engine()
    except Exception as e:
        # If query engine initialization fails, return error message
        # Ensure error message is a safe string
        error_msg = str(e) if e else "Unknown error"
        logger.error(f"Error initializing query engine: {error_msg}")
        return [TextContent(
            type="text",
            text=f"Error: Failed to initialize query engine. {error_msg}",
        )]
    
    if name == "query_wpilib_docs":
        if not arguments:
            return [TextContent(
                type="text",
                text="Error: Missing required arguments",
            )]
        
        question = arguments.get("question")
        version = arguments.get("version")
        language = arguments.get("language")
        
        if not question:
            return [TextContent(
                type="text",
                text="Error: 'question' parameter is required",
            )]
        
        if not version:
            return [TextContent(
                type="text",
                text="Error: 'version' parameter is required",
            )]
        
        if not language:
            return [TextContent(
                type="text",
                text=f"Error: 'language' parameter is required. Supported languages: {', '.join(SUPPORTED_LANGUAGES)}",
            )]
        
        if language not in SUPPORTED_LANGUAGES:
            return [TextContent(
                type="text",
                text=f"Error: Unsupported language '{language}'. Supported languages: {', '.join(SUPPORTED_LANGUAGES)}",
            )]
        
        try:
            response = engine.query(
                question=question,
                version=version,
                language=language,
            )
            return [TextContent(
                type="text",
                text=response,
            )]
        except ValueError as e:
            return [TextContent(
                type="text",
                text=f"Error: {str(e)}",
            )]
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"Error querying documentation: {str(e)}",
            )]
    
    elif name == "list_available_versions":
        try:
            versions = engine.get_available_versions()
            if not versions:
                return [TextContent(
                    type="text",
                    text="No versions found in database. Please run ingestion first.",
                )]
            return [TextContent(
                type="text",
                text=f"Available WPILib versions: {', '.join(versions)}",
            )]
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"Error listing versions: {str(e)}",
            )]
    
    elif name == "get_latest_version":
        try:
            latest = engine.get_latest_version()
            return [TextContent(
                type="text",
                text=latest,
            )]
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"Error getting latest version: {str(e)}",
            )]
    
    elif name == "list_available_languages":
        try:
            version = arguments.get("version") if arguments else None
            languages = engine.get_available_languages(version=version)
            if not languages:
                version_text = f" for version {version}" if version else ""
                return [TextContent(
                    type="text",
                    text=f"No languages found{version_text}",
                )]
            version_text = f" for version {version}" if version else ""
            return [TextContent(
                type="text",
                text=f"Available languages{version_text}: {', '.join(languages)}",
            )]
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"Error listing languages: {str(e)}",
            )]
    
    elif name == "embed_query":
        if not arguments:
            return [TextContent(
                type="text",
                text="Error: Missing required arguments",
            )]
        
        query = arguments.get("query")
        if not query:
            return [TextContent(
                type="text",
                text="Error: 'query' parameter is required",
            )]
        
        try:
            response = engine.embed_query(query)
            return [TextContent(
                type="text",
                text=response,
            )]
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"Error generating embedding: {str(e)}",
            )]
    
    else:
        return [TextContent(
            type="text",
            text=f"Unknown tool: {name}",
        )]


async def main():
    """Main entry point for MCP server."""
    # Suppress any environment variables that might cause libraries to print
    os.environ['PYTHONUNBUFFERED'] = '0'  # Keep stdout buffered for JSON-RPC
    os.environ['PYTHONWARNINGS'] = 'ignore'  # Suppress Python warnings
    
    # Suppress warnings to stderr as well
    import warnings
    warnings.filterwarnings('ignore')
    
    try:
        async with stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options(),
            )
    except KeyboardInterrupt:
        # Clean shutdown on Ctrl+C
        sys.exit(0)
    except Exception as e:
        # Log error to stderr only
        logger.critical(f"Fatal error: {str(e)[:200]}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

