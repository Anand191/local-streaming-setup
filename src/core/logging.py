import sys

from loguru import logger

# Remove default handler
logger.remove()

# Add a new handler to stderr with INFO level
logger.add(
    sys.stderr,
    level="INFO",
    format=(
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    ),
)

# Export the configured logger
__all__ = ["logger"]
