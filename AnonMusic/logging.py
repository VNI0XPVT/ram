import logging
from logging.handlers import RotatingFileHandler
import os

LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
LOG_FILE = "log.txt"

try:
    # Set up rotating log file (5MB max, 3 backups)
    file_handler = RotatingFileHandler(LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=3)
    file_handler.setFormatter(logging.Formatter(
        "[%(asctime)s - %(levelname)s] - %(name)s - %(message)s",
        datefmt="%d-%b-%y %H:%M:%S"
    ))

    # Set up console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(
        "[%(asctime)s - %(levelname)s] - %(name)s - %(message)s",
        datefmt="%d-%b-%y %H:%M:%S"
    ))

    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL, logging.INFO),
        handlers=[file_handler, console_handler]
    )

    # Suppress excessive logging from dependencies
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("pyrogram").setLevel(logging.WARNING)
    logging.getLogger("pytgcalls").setLevel(logging.WARNING)

except Exception as e:
    print(f"Logging setup failed: {e}")
    logging.basicConfig(level=logging.INFO)  # fallback

def LOGGER(name: str) -> logging.Logger:
    try:
        return logging.getLogger(name)
    except Exception:
        return logging.getLogger("AnonX")  # fallback logger
