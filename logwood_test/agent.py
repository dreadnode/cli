import os
import sys
import traceback
from datetime import datetime

# Add these at the very top after imports
print("=== Starting agent.py ===", file=sys.stderr)
print(f"Python version: {sys.version}", file=sys.stderr)
print(f"Current working directory: {os.getcwd()}", file=sys.stderr)
print(f"Contents of current directory: {os.listdir('.')}", file=sys.stderr)
print(f"Environment variables: {dict(os.environ)}", file=sys.stderr)

import typing as t
from urllib.parse import quote
import asyncio

import httpx
import rigging as rg
from loguru import logger
from pydantic import BaseModel, Field

# Add these at the very top after imports
print("=== Starting agent.py ===", file=sys.stderr)
start_time = datetime.now()

# Configure loguru with more detailed formatting
logger.remove()  # Remove default handler
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="DEBUG",
    backtrace=True,
    diagnose=True
)

GUIDANCE = os.getenv("GUIDANCE", "default_guidance")

async def list_files():
    # Implement this function based on your needs
    pass

async def main() -> None:
    try:
        logger.info("Starting agent 'logwood'")
        logger.info(f"Guidance: {GUIDANCE}")

        # Test connectivity to fileshare
        try:
            directory_content = await list_files()
            logger.info(f"Initial directory listing found {len(directory_content.files)} files")
            logger.debug(f"Files: {directory_content.files}")
        except Exception as e:
            logger.error(f"Failed to list files: {e}")
            logger.debug(f"Exception details: {traceback.format_exc()}")
            raise

        # Test connectivity to dropship
        try:
            logger.info("Testing connection to dropship...")
            async with httpx.AsyncClient() as client:
                response = await client.get("http://dropship/health")
                logger.info(f"Dropship health check status: {response.status_code}")
        except Exception as e:
            logger.error(f"Failed to connect to dropship: {e}")
            logger.debug(f"Exception details: {traceback.format_exc()}")
            raise

        # Rest of your existing main() code...

    except Exception as e:
        logger.error(f"Fatal error in main: {str(e)}")
        logger.debug(f"Exception details: {traceback.format_exc()}")
        raise
    finally:
        end_time = datetime.now()
        duration = end_time - start_time
        logger.info(f"Agent execution completed. Duration: {duration.total_seconds():.2f}s")
        # Sleep briefly to ensure logs are flushed
        await asyncio.sleep(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Failed to run main: {str(e)}")
        logger.debug(f"Exception details: {traceback.format_exc()}")
        sys.exit(1)