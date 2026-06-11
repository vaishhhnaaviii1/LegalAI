import logging
import sys
from pathlib import Path

def setup_logging():
    # Ensure a logs directory exists
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "legalai.log"

    # Define the log format
    log_format = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # 1. File Handler (saves to logs/legalai.log)
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(log_format)
    file_handler.setLevel(logging.INFO)

    # 2. Console Handler (prints to terminal)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_format)
    console_handler.setLevel(logging.INFO)

    # 3. Configure the Root Logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    # it ignores ultra-low-level DEBUG spam but captures INFO, WARNING, ERROR, and CRITICAL messages.
    
    # Avoid adding handlers multiple times if imported twice
    if not root_logger.handlers:
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)

    return logging.getLogger(__name__)