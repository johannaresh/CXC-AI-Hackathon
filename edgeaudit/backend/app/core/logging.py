import logging
import sys

from .config import settings


def setup_logging() -> logging.Logger:
    logger = logging.getLogger("edgeaudit")
    logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter("%(asctime)s | %(levelname)-8s | %(name)s | %(message)s")
    )
    logger.addHandler(handler)
    return logger


logger = setup_logging()
