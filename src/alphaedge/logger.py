"""
Logging configuration for AlphaEdge using Loguru.
"""

import sys
from loguru import logger
from alphaedge.config import settings

# Remove default handler
logger.remove()

# Console handler
logger.add(
    sys.stderr,
    level=settings.log_level,
    format=(
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    ),
    colorize=True,
)

# File handler
try:
    log_path = settings.log_dir / "alphaedge.log"
    logger.add(
        str(log_path),
        level=settings.log_level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation=settings.log_rotation,
        retention=settings.log_retention,
        compression="zip",
    )
except Exception:
    pass  # Non-fatal: skip file logging if dir unavailable

# Public alias
log = logger
