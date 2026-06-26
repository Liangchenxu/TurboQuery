"""Unified logging configuration for TurboQuery.

Provides a function to configure the root logger with a consistent format,
supporting both INFO and DEBUG verbosity levels.
"""

import logging
import sys
from typing import Optional


def setup_logger(verbose: bool = False, name: Optional[str] = None) -> logging.Logger:
    """Configure and return a logger instance with unified formatting.

    Args:
        verbose: If True, set logging level to DEBUG; otherwise INFO.
        name: Optional logger name. If None, returns the root logger.

    Returns:
        A configured logging.Logger instance.

    Examples:
        >>> logger = setup_logger(verbose=True, name="loader")
        >>> logger.debug("Detailed debug information")
    """
    level = logging.DEBUG if verbose else logging.INFO
    target_logger = logging.getLogger(name)

    # Avoid adding duplicate handlers if already configured.
    if not target_logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)-7s] %(name)-12s %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        target_logger.addHandler(handler)

    target_logger.setLevel(level)
    # Prevent propagation to root if this is a named logger.
    if name is not None:
        target_logger.propagate = False

    return target_logger


if __name__ == "__main__":
    # Simple self-test: output messages at both levels.
    log = setup_logger(verbose=True, name="logger_test")
    log.debug("This is a DEBUG message — verbose mode.")
    log.info("This is an INFO message.")
    log.warning("This is a WARNING message.")