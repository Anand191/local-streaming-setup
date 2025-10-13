import asyncio
from typing import Any

from core.logging import logger


async def heavy_processing(payload: dict[str, Any]) -> dict[str, Any]:
    """Simulates a heavy and time-consuming processing task."""
    logger.info(f"Starting heavy processing for payload: {payload}")
    # Simulate a long-running task
    await asyncio.sleep(10)
    result = {"processed_data": f"Processed {payload.get('data', 'N/A')}"}
    logger.info(f"Finished heavy processing. Result: {result}")
    return result
