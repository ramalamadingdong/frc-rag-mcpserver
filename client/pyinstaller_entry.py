"""
PyInstaller entry point for wpilib-rag-server
This avoids relative import issues when building the executable.
"""
import asyncio
import sys
import os

# Ensure the package can be imported
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from wpilib_rag.server import main as async_main


def main():
    """Entry point for the executable."""
    asyncio.run(async_main())


if __name__ == "__main__":
    main()

