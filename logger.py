# logger.py
import logging
import sys
from pythonjsonlogger import jsonlogger

def get_logger(name: str) -> logging.Logger:
    """
    Configures and returns a logger that outputs structured JSON.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Prevent logs from being propagated to the root logger, which can cause duplicates.
    logger.propagate = False

    # If a handler is already configured, don't add another one.
    if not logger.handlers:
        logHandler = logging.StreamHandler(sys.stdout) # Log to standard output

        # Use a JSON formatter
        formatter = jsonlogger.JsonFormatter(
            '%(asctime)s %(name)s %(levelname)s %(message)s'
        )
        logHandler.setFormatter(formatter)
        logger.addHandler(logHandler)

    return logger
