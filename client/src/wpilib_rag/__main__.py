"""Entry point for running server module as a package."""

import asyncio
from .server import main as async_main


def main():
    """Synchronous entry point for console script."""
    asyncio.run(async_main())


if __name__ == "__main__":
    main()

