"""统一日志配置。"""

from __future__ import annotations

import logging
import sys

_FORMAT = "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"


def setup_logging(level: int = logging.INFO) -> None:
    logging.basicConfig(level=level, format=_FORMAT, stream=sys.stderr, force=True)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
