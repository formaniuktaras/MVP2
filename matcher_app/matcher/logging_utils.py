"""Налаштування логування для MatcherApp."""
from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

LOG_FILE_NAME = "matcher.log"


def setup_logging(base_dir: Optional[Path] = None) -> logging.Logger:
    """Створює та повертає логер застосунку."""
    if base_dir is None:
        base_dir = Path.cwd()
    log_path = base_dir / LOG_FILE_NAME
    logger = logging.getLogger("matcher_app")
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    handler = RotatingFileHandler(log_path, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)
    logger.propagate = False
    logger.info("Логування ініціалізовано")
    return logger
