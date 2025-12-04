"""Database loader for downloading ChromaDB from server with version tracking.

IMPORTANT: Database downloads do NOT require any API key authentication.
The download endpoint is public and can be accessed without authentication.
"""

import os
import shutil
import tarfile
import tempfile
import logging
from pathlib import Path
from typing import Optional, Dict

try:
    import requests
    from tqdm import tqdm
except ImportError:
    # These should be available via dependencies, but handle gracefully
    requests = None
    tqdm = None

logger = logging.getLogger(__name__)

# Version tracking file stored alongside database
DB_VERSION_FILE = ".db_version"


def fix_database_permissions(local_path: str) -> bool:
    """Fix permissions on database files to ensure they're writable.
    
    This function aggressively fixes permissions on all database files and directories,
    including the parent directory, to ensure ChromaDB can write to the database.
    
    Args:
        local_path: Path to local database directory
    
    Returns:
        True if permissions were fixed successfully, False otherwise
    """
    local_path_obj = Path(local_path)
    
    if not local_path_obj.exists():
        return False
    
    try:
        # First, fix parent directory permissions (important for macOS)
        parent = local_path_obj.parent
        if parent.exists():
            try:
                os.chmod(parent, 0o755)
            except Exception as e:
                logger.warning(f"Could not fix permissions for parent directory: {e}")
        
        # Fix permissions - make all files and directories writable by owner
        # Use os.walk with topdown=False to process children before parents
        for root, dirs, files in os.walk(local_path_obj, topdown=False):
            # Fix files first
            for f in files:
                file_path = os.path.join(root, f)
                try:
                    # Make file writable by owner (644 = rw-r--r--)
                    os.chmod(file_path, 0o644)
                    # Verify it's writable
                    if not os.access(file_path, os.W_OK):
                        logger.warning(f"File {f} is still not writable after chmod")
                except Exception as e:
                    logger.warning(f"Could not fix permissions for file {f}: {e}")
            
            # Then fix directories
            for d in dirs:
                dir_path = os.path.join(root, d)
                try:
                    # Make directory writable by owner (755 = rwxr-xr-x)
                    os.chmod(dir_path, 0o755)
                except Exception as e:
                    logger.warning(f"Could not fix permissions for directory {d}: {e}")
        
        # Finally, fix the database directory itself
        try:
            os.chmod(local_path_obj, 0o755)
        except Exception as e:
            logger.warning(f"Could not fix permissions for database directory: {e}")
        
        # Verify critical files are writable
        sqlite_file = local_path_obj / "chroma.sqlite3"
        if sqlite_file.exists() and not os.access(sqlite_file, os.W_OK):
            logger.error(f"SQLite file is still not writable after permission fix!")
            return False
        
        logger.info(f"Fixed permissions for database at {local_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to fix database permissions: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def download_database(
    db_url: str,
    local_path: str,
    force_download: bool = False,
) -> bool:
    """Download ChromaDB from server.
    
    NOTE: This function does NOT require any API key or authentication.
    The database download endpoint is public.
    
    Args:
        db_url: URL to the database archive (tar.gz) on your server
        local_path: Local path where database should be stored
        force_download: If True, re-download even if database exists
    
    Returns:
        True if download successful, False otherwise
    """
    local_path_obj = Path(local_path)
    
    # Check if database already exists
    if local_path_obj.exists() and not force_download:
        logger.info(f"Database already exists at {local_path}")
        return True
    
    # Create parent directory if it doesn't exist
    local_path_obj.parent.mkdir(parents=True, exist_ok=True)
    
    # Check dependencies
    if requests is None:
        logger.error("requests library not available. Cannot download database.")
        return False
    
    # Download database archive
    logger.info(f"Downloading database from {db_url}...")
    
    tmp_path = None
    temp_base_dir = local_path_obj.parent
    temp_base_dir.mkdir(parents=True, exist_ok=True)
    try:
        # Download with progress bar if tqdm available
        response = requests.get(db_url, stream=True, timeout=300)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        
        # Save to temporary file (ensure it's within our writable directory)
        with tempfile.NamedTemporaryFile(delete=False, suffix='.tar.gz', dir=temp_base_dir) as tmp_file:
            tmp_path = tmp_file.name
            
            if tqdm and total_size > 0:
                with tqdm(total=total_size, unit='B', unit_scale=True, desc="Downloading") as pbar:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            tmp_file.write(chunk)
                            pbar.update(len(chunk))
            else:
                # Download without progress bar
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        tmp_file.write(chunk)
        
        # Extract archive
        logger.info("Extracting database...")
        with tarfile.open(tmp_path, 'r:gz') as tar:
            # Extract to temporary directory first (use same writable base)
            with tempfile.TemporaryDirectory(dir=temp_base_dir) as tmp_extract_dir:
                # Use secure extraction when available (Python >=3.12)
                try:
                    tar.extractall(tmp_extract_dir, filter='data')
                except TypeError:
                    # Fallback for Python versions without filter parameter
                    tar.extractall(tmp_extract_dir)
                
                # Find the chroma_db directory in the extracted files
                extracted_paths = list(Path(tmp_extract_dir).rglob('chroma_db'))
                if not extracted_paths:
                    # Try to find any directory that looks like a chroma database
                    extracted_paths = [d for d in Path(tmp_extract_dir).iterdir() if d.is_dir()]
                
                if not extracted_paths:
                    raise ValueError("Could not find chroma_db directory in archive")
                
                # Copy the database to the target location
                source_db = extracted_paths[0]
                if local_path_obj.exists():
                    shutil.rmtree(local_path_obj)
                
                # Use copytree instead of move to avoid permission issues with temp directories
                shutil.copytree(str(source_db), str(local_path_obj))
                
                # Fix permissions immediately after copying to ensure database is writable
                if not fix_database_permissions(str(local_path_obj)):
                    logger.warning("Failed to fix permissions after database download - database may be read-only")
        
        # Clean up temporary archive
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)
        
        # Ensure permissions are correct one more time before returning
        fix_database_permissions(local_path)
        
        logger.info(f"Database successfully downloaded to {local_path}")
        return True
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to download database: {e}")
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)
        return False
    except Exception as e:
        logger.error(f"Failed to extract database: {e}")
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)
        return False


def get_local_db_version(local_path: str) -> str:
    """Get version of locally installed database.
    
    Args:
        local_path: Path to local database directory
    
    Returns:
        Version string or "unknown" if not found
    """
    version_file = Path(local_path) / DB_VERSION_FILE
    if not version_file.exists():
        return "unknown"
    try:
        return version_file.read_text().strip()
    except Exception as e:
        logger.warning(f"Could not read version file: {e}")
        return "unknown"


def save_db_version(local_path: str, version: str):
    """Save database version to local version file.
    
    Args:
        local_path: Path to local database directory
        version: Version string to save
    """
    version_file = Path(local_path) / DB_VERSION_FILE
    try:
        version_file.write_text(version)
        logger.info(f"Saved database version: {version}")
    except Exception as e:
        logger.warning(f"Could not save version file: {e}")


def get_remote_db_version(proxy_url: str) -> Optional[Dict]:
    """Check server for latest database version.
    
    Args:
        proxy_url: Base URL of the proxy service
    
    Returns:
        Dictionary with version info or None if failed
    """
    if not requests:
        logger.error("requests library not available")
        return None
    
    try:
        # Remove trailing slash and /database/download from URL
        base_url = proxy_url.rstrip('/').replace('/database/download', '')
        version_url = f"{base_url}/database/version"
        
        response = requests.get(version_url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.warning(f"Could not check remote database version: {e}")
        return None
    except Exception as e:
        logger.warning(f"Error parsing remote version info: {e}")
        return None


def check_for_updates(local_path: str, proxy_url: str) -> Optional[Dict]:
    """Check if database needs updating.
    
    Args:
        local_path: Path to local database directory
        proxy_url: Base URL of the proxy service
    
    Returns:
        Dictionary with update info if update available, None otherwise
    """
    # If database doesn't exist, it needs to be downloaded
    if not Path(local_path).exists():
        remote_info = get_remote_db_version(proxy_url)
        if remote_info:
            return {
                "action": "install",
                "current_version": None,
                "new_version": remote_info["version"],
                "size_mb": remote_info["size_mb"],
                "changelog": remote_info.get("changelog", ""),
            }
        return None
    
    # Check versions
    local_version = get_local_db_version(local_path)
    remote_info = get_remote_db_version(proxy_url)
    
    if not remote_info:
        return None
    
    if local_version != remote_info["version"]:
        return {
            "action": "update",
            "current_version": local_version,
            "new_version": remote_info["version"],
            "size_mb": remote_info["size_mb"],
            "changelog": remote_info.get("changelog", ""),
        }
    
    return None


def ensure_database(db_url: Optional[str], local_path: str, proxy_url: Optional[str] = None, auto_update: bool = False) -> bool:
    """Ensure database exists locally, downloading if necessary.
    
    NOTE: Database downloads do NOT require any API key or authentication.
    
    Args:
        db_url: URL to database archive on your server (None to skip download)
        local_path: Local path where database should be stored
        proxy_url: Base URL of server for version checking (optional, no auth required)
        auto_update: If True, automatically update when new version available
    
    Returns:
        True if database exists locally, False otherwise
    """
    local_path_obj = Path(local_path)
    
    # Check for updates if proxy URL provided
    if proxy_url and auto_update:
        update_info = check_for_updates(local_path, proxy_url)
        if update_info:
            logger.info(f"Database update available: {update_info['current_version']} → {update_info['new_version']}")
            logger.info(f"Downloading update ({update_info['size_mb']} MB)...")
            if download_database(db_url, local_path, force_download=True):
                save_db_version(local_path, update_info['new_version'])
                return True
            return False
    
    # If database exists, we're good
    if local_path_obj.exists():
        return True
    
    # If no URL provided, can't download
    if not db_url:
        logger.warning(f"No database URL provided and database not found at {local_path}")
        return False
    
    # Try to download
    success = download_database(db_url, local_path)
    
    # Save version if download successful and we can check remote version
    if success and proxy_url:
        remote_info = get_remote_db_version(proxy_url)
        if remote_info:
            save_db_version(local_path, remote_info['version'])
    
    return success


def update_database_cli():
    """CLI command to manually update database."""
    from .config import CHROMA_DB_PATH, CLOUD_DB_URL
    
    print("=" * 60)
    print("WPILib RAG Database Update")
    print("=" * 60)
    
    if not CLOUD_DB_URL:
        print("Error: No database download URL configured")
        print("Set CLOUD_DB_URL environment variable")
        return 1
    
    # Extract base URL from CLOUD_DB_URL for version checking
    base_url = CLOUD_DB_URL.rstrip('/').replace('/database/download', '')
    
    print("\nChecking for updates...")
    update_info = check_for_updates(CHROMA_DB_PATH, base_url)
    
    if not update_info:
        current_version = get_local_db_version(CHROMA_DB_PATH)
        print(f"✓ Already up to date (version {current_version})")
        return 0
    
    # Display update info
    print()
    if update_info['action'] == 'install':
        print(f"Installing database version {update_info['new_version']}")
    else:
        print(f"Update available:")
        print(f"  Current: {update_info['current_version']}")
        print(f"  New:     {update_info['new_version']}")
    
    print(f"  Size:    {update_info['size_mb']} MB")
    if update_info['changelog']:
        print(f"  Changes: {update_info['changelog']}")
    
    # Confirm
    print()
    try:
        response = input("Continue? [y/N]: ").strip().lower()
        if response != 'y':
            print("Cancelled.")
            return 0
    except (KeyboardInterrupt, EOFError):
        print("\nCancelled.")
        return 0
    
    # Download
    print("\nDownloading...")
    if download_database(CLOUD_DB_URL, CHROMA_DB_PATH, force_download=True):
        save_db_version(CHROMA_DB_PATH, update_info['new_version'])
        print()
        print("=" * 60)
        print(f"✓ Update complete! (version {update_info['new_version']})")
        print("=" * 60)
        return 0
    else:
        print("\nUpdate failed. Check logs for details.")
        return 1

