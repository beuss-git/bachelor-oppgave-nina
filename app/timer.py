"""A timer class to time code blocks."""
import time
from typing import Any

from app.logger import get_logger

logger = get_logger()


class Timer:
    """A timer class to time code blocks."""

    def __init__(self, name: str) -> None:
        self.name: str = name
        self.start: float = 0

    def __enter__(self) -> None:
        self.start = time.time()

    def __exit__(self, exc_type: Any, exc_value: Any, exc_traceback: Any) -> None:
        if exc_type is not None:
            # logger.error("Exception raised in timer block", exc_info=True)
            return

        delta_time = time.time() - self.start

        logger.info("%s took %s seconds", self.name, delta_time)
