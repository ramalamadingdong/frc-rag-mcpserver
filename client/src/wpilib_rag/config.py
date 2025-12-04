"""Configuration and Chroma initialization for WPILib RAG system."""

import os
import sys
import logging
from typing import Optional
from pathlib import Path

import chromadb
from chromadb.config import Settings
from dotenv import load_dotenv

from .database_loader import ensure_database, check_for_updates, fix_database_permissions


class DatabaseNotFoundError(Exception):
    """Raised when database is not found and cannot be downloaded."""
    pass

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# API Keys
# IMPORTANT: API keys are ONLY needed for embedding generation.
# Database downloads from your server do NOT require any API key.
#
# For embedding generation, users MUST provide VOYAGE_API_KEY.
# Set the VOYAGE_API_KEY environment variable for direct Voyage AI API access.

VOYAGE_API_KEY = os.getenv("VOYAGE_API_KEY") or os.getenv("WPILIB_RAG_VOYAGE_API_KEY")

# Configuration defaults
# For executables, use a path relative to the executable or a user data directory
# For regular Python scripts, use current directory
if getattr(sys, 'frozen', False):
    # Running as compiled executable (PyInstaller, cx_Freeze, etc.)
    # Use a path relative to the executable location
    if sys.platform == "win32":
        # Windows: Use AppData/Local
        appdata = os.getenv("LOCALAPPDATA", os.path.expanduser("~/.local"))
        CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", os.path.join(appdata, "wpilib-rag", "chroma_db"))
    else:
        # macOS: Prefer ~/Library/Application Support (fallback to XDG_DATA_HOME if set)
        default_data_dir = Path(os.getenv("XDG_DATA_HOME", Path.home() / "Library" / "Application Support"))
        CHROMA_DB_PATH = os.getenv(
            "CHROMA_DB_PATH",
            str(default_data_dir / "wpilib-rag" / "chroma_db"),
        )
else:
    # Running as regular Python script
    CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", "./chroma_db")

# Ensure the parent directory exists (ignore errors if this fails; handled later)
try:
    Path(CHROMA_DB_PATH).parent.mkdir(parents=True, exist_ok=True)
except Exception:
    pass

VOYAGE_MODEL = os.getenv("VOYAGE_MODEL", "voyage-code-3")

# Server configuration
# Hardcoded server URL - this is where the client will download the database.
# Database downloads do NOT require any API key - the endpoint is public.
SERVER_URL = "http://97.139.150.106:3000"

# Database download configuration
# This is the URL where the ChromaDB database archive can be downloaded.
# NO API KEY is required for database downloads - the endpoint is public.
#
# Automatically constructed from server URL. Can be overridden via CLOUD_DB_URL environment variable.
CLOUD_DB_URL = os.getenv("CLOUD_DB_URL", f"{SERVER_URL.rstrip('/')}/database/download")

# Auto-update configuration
# Automatically download database updates on startup (default: true)
# Set to "false" to disable automatic updates
AUTO_UPDATE_DB = os.getenv("WPILIB_RAG_AUTO_UPDATE", "true").lower() == "true"

# Chroma collection name
COLLECTION_NAME = "wpilib_docs"

# Default/latest version
DEFAULT_VERSION = os.getenv("DEFAULT_WPILIB_VERSION", "2025")

# Query defaults
DEFAULT_TOP_K = 8

# Supported languages
# Note: Both "C++" and "cpp" are accepted - query engine maps "cpp" to "C++" for database queries
SUPPORTED_LANGUAGES = ["Java", "Python", "C++", "cpp", "API Reference"]


def get_chroma_client() -> chromadb.ClientAPI:
    """Initialize and return Chroma client with persistent storage.
    
    Automatically downloads database from your server if it doesn't exist locally.
    Database downloads do NOT require any API key - the download endpoint is public.
    """
    # Check for updates and notify user (non-intrusive)
    # Extract base URL from CLOUD_DB_URL for version checking
    proxy_url_for_version_check = None
    if CLOUD_DB_URL:
        # Remove /database/download from end if present
        proxy_url_for_version_check = CLOUD_DB_URL.rstrip('/').replace('/database/download', '')
    
    if proxy_url_for_version_check and CLOUD_DB_URL:
        if Path(CHROMA_DB_PATH).exists():
            # Only check for updates if database already exists
            # (first install is handled by ensure_database below)
            update_info = check_for_updates(CHROMA_DB_PATH, proxy_url_for_version_check)
            if update_info and update_info['action'] == 'update':
                logger.warning(
                    f"\n{'='*60}\n"
                    f"Database update available!\n"
                    f"  Current: {update_info['current_version']}\n"
                    f"  New:     {update_info['new_version']}\n"
                    f"  Size:    {update_info['size_mb']} MB\n"
                )
                if update_info['changelog']:
                    logger.warning(f"  Changes: {update_info['changelog']}\n")
                
                if AUTO_UPDATE_DB:
                    logger.warning("  Auto-updating... (WPILIB_RAG_AUTO_UPDATE=true)\n" + "="*60)
                else:
                    logger.warning(
                        f"  To update: Run 'wpilib-rag-update'\n"
                        f"  Or set: WPILIB_RAG_AUTO_UPDATE=true\n"
                        f"{'='*60}"
                    )
    
    # Ensure database exists (download from cloud if needed, with auto-update)
    db_path_obj = Path(CHROMA_DB_PATH)
    
    if not db_path_obj.exists():
        if CLOUD_DB_URL:
            # Try to download the database
            logger.info(f"Database not found at {CHROMA_DB_PATH}. Attempting to download...")
            if not ensure_database(
                CLOUD_DB_URL, 
                CHROMA_DB_PATH, 
                proxy_url=proxy_url_for_version_check,
                auto_update=AUTO_UPDATE_DB
            ):
                # Download failed
                error_msg = (
                    f"Database not found at {CHROMA_DB_PATH} and download failed.\n"
                    f"Download URL: {CLOUD_DB_URL}\n"
                    "Please check your network connection and ensure the database URL is accessible."
                )
                logger.error(error_msg)
                raise DatabaseNotFoundError(error_msg)
        else:
            # No download URL configured and database doesn't exist
            error_msg = (
                f"No database download URL configured and database not found at {CHROMA_DB_PATH}.\n"
                f"To download from your server, set the CLOUD_DB_URL environment variable:\n"
                f"  CLOUD_DB_URL=\"https://your-server.com/database/download\"\n"
                f"Note: Database downloads do NOT require any API key."
            )
            logger.error(error_msg)
            raise DatabaseNotFoundError(error_msg)
    
    # Verify database is actually a valid ChromaDB directory (after potential download)
    # At this point, db_path_obj should exist (either it existed or we just downloaded it)
    if not db_path_obj.exists():
        error_msg = (
            f"Database path {CHROMA_DB_PATH} does not exist after download attempt.\n"
            "Please check the download URL and try again."
        )
        logger.error(error_msg)
        raise DatabaseNotFoundError(error_msg)
    
    if not db_path_obj.is_dir():
        error_msg = (
            f"Database path {CHROMA_DB_PATH} exists but is not a valid ChromaDB directory.\n"
            "Please ensure the database was properly downloaded and extracted."
        )
        logger.error(error_msg)
        raise DatabaseNotFoundError(error_msg)
    
    # Fix permissions on existing database to ensure it's writable
    # This handles cases where the database was extracted with read-only permissions
    # We do this BEFORE opening ChromaDB to prevent "readonly database" errors
    if not fix_database_permissions(CHROMA_DB_PATH):
        logger.warning("Permission fix failed - database may be read-only. ChromaDB operations may fail.")
    else:
        logger.debug("Database permissions verified and fixed")
    
    client = chromadb.PersistentClient(
        path=CHROMA_DB_PATH,
        settings=Settings(
            anonymized_telemetry=False,
            allow_reset=True,
        ),
    )
    return client


def get_or_create_collection(
    client: Optional[chromadb.ClientAPI] = None,
) -> chromadb.Collection:
    """Get or create the wpilib_docs collection."""
    if client is None:
        client = get_chroma_client()
    
    # Get or create collection
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"description": "WPILib documentation with version and language metadata"},
    )
    
    return collection


def validate_embedding_keys() -> tuple[bool, Optional[str]]:
    """Validate that embedding generation is available.
    
    Requires VOYAGE_API_KEY for direct Voyage AI API access.
    If not configured, embedding generation will fail.
    """
    if not VOYAGE_API_KEY:
        return False, (
            "Voyage AI API key is REQUIRED for embedding generation.\n"
            "Set the VOYAGE_API_KEY environment variable:\n"
            "  export VOYAGE_API_KEY=\"your-api-key-here\""
        )
    return True, None

