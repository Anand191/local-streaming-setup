from typing import Any

from core.logging import logger
from services.processing import heavy_processing


async def process_sync(payload: dict[str, Any]) -> dict[str, Any]:
    """Simulates a synchronous REST EP that blocks until processing is complete."""
    logger.info("Starting synchronous REST processing...")
    # This await simulates a blocking I/O call in a real-world scenario.
    # In a purely synchronous framework (like standard Flask), this would
    # block the entire worker thread.
    result = await heavy_processing(payload)
    logger.info("Synchronous REST processing finished.")
    return result
