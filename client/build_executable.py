#!/usr/bin/env python3
"""
Build standalone executables for wpilib-rag-server
Creates executables for Windows and macOS
"""
import warnings
import sys
import os
from pathlib import Path

# Suppress warnings during build
warnings.filterwarnings('ignore')
os.environ['PYTHONWARNINGS'] = 'ignore'

import PyInstaller.__main__

def build_executable():
    """Build standalone executable using PyInstaller."""
    
    # Change to the client directory to ensure relative paths work
    original_cwd = os.getcwd()
    build_dir = Path(__file__).parent
    os.chdir(build_dir)
    
    try:
        # PyInstaller arguments
        args = [
            'pyinstaller_entry.py',          # Entry point (no relative imports)
            '--name=wpilib-rag-server',      # Executable name
            '--console',                      # Console application
            '--clean',                        # Clean build
            
            # Add the source directory to the Python path
            '--paths=src',
            
            # Include all dependencies
            '--hidden-import=voyageai',
            '--hidden-import=chromadb',
            '--hidden-import=chromadb.config',
            '--hidden-import=chromadb.utils',
            '--hidden-import=mcp',
            '--hidden-import=mcp.server',
            '--hidden-import=mcp.server.stdio',
            '--hidden-import=sqlite3',
            '--hidden-import=pydantic',
            '--hidden-import=pydantic_core',
            
            # Collect all submodules
            '--collect-all=chromadb',
            '--collect-all=mcp',
        ]
        
        # Platform-specific options
        if sys.platform == "win32":
            # Windows: Use --onedir to avoid temp extraction issues
            args.extend([
                '--onedir',                     # Create a folder instead of single file
            ])
        elif sys.platform == "darwin":
            # macOS: Use --onefile now that temp paths are controlled
            args.extend([
                '--onefile',
                '--strip',
                '--noupx',
            ])
        else:
            raise RuntimeError(f"Unsupported platform for build: {sys.platform}. Only Windows and macOS are supported.")
        
        print("Building executable...")
        print(f"Platform: {sys.platform}")
        print(f"Working directory: {os.getcwd()}")
        
        try:
            PyInstaller.__main__.run(args)
        except Exception as e:
            print(f"\n{'='*60}")
            print("Build failed with error:")
            print(f"{'='*60}")
            import traceback
            traceback.print_exc()
            print(f"\n{'='*60}")
            print("Troubleshooting:")
            print("1. Ensure all dependencies are installed: uv sync --extra dev")
            print("2. Try running from the client directory: cd client && uv run build_executable.py")
            print("3. Check that pyinstaller_entry.py exists in the client directory")
            print("4. On Windows, try running as administrator or check antivirus settings")
            print(f"{'='*60}")
            raise
    finally:
        # Restore original working directory
        os.chdir(original_cwd)
    
    print("\n" + "="*60)
    print("Build complete!")
    print("="*60)
    
    dist_dir = Path("dist")
    if sys.platform == "win32":
        # Windows uses --onedir, so the exe is in a subdirectory
        exe_name = "wpilib-rag-server.exe"
        exe_path = dist_dir / "wpilib-rag-server" / exe_name
    elif sys.platform == "darwin":
        # macOS uses --onefile, so the binary is directly in dist
        exe_name = "wpilib-rag-server"
        exe_path = dist_dir / exe_name
    else:
        raise RuntimeError(f"Unsupported platform for build: {sys.platform}. Only Windows and macOS are supported.")
    
    if exe_path.exists():
        print(f"\nExecutable created: {exe_path}")
        print(f"Size: {exe_path.stat().st_size / 1024 / 1024:.1f} MB")
        print("\nTo use in MCP config:")
        if sys.platform == "win32":
            print(f'  "command": "{exe_path.absolute()}"')
            print("\nNote: Windows uses --onedir mode (folder with .exe)")
            print(f"      All files are in: {exe_path.parent}")
        elif sys.platform == "darwin":
            print(f'  "command": "{exe_path.absolute()}"')
            print("\nNote: macOS uses --onefile mode (single executable)")
        else:
            print(f'  "command": "{exe_path.absolute()}"')
    else:
        print("\nWarning: Executable not found at expected location")

if __name__ == "__main__":
    build_executable()

