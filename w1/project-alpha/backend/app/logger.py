import logging
import sys
import time
from typing import Any, Dict

from .config import settings


def setup_logging() -> None:
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        handlers=[logging.StreamHandler(sys.stdout)],
        format="%(message)s",
    )


def json_log(
    message: str, extra: Dict[str, Any] | None = None, level: int = logging.INFO
) -> None:
    payload = {"message": message, **(extra or {})}
    logging.log(level, payload)


class RequestTimer:
    def __enter__(self) -> "RequestTimer":
        self.start = time.perf_counter()
        return self

    def __exit__(self, *exc: object) -> None:
        self.duration = (time.perf_counter() - self.start) * 1000
