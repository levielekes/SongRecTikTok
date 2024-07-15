import logging
import os

from logging.handlers import RotatingFileHandler

from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

BASE_LOG_FILE_PATH = os.getenv('LOG_FILE_PATH')


def configure_logger(name: str = 'songrec') -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Create formatters and add them to handlers
    verbose_formatter = logging.Formatter(
        '%(levelname)s - %(asctime)s - %(pathname)s - [%(lineno)d] - [%(process)d] --> %(message)s')
    simple_formatter = logging.Formatter('%(levelname)s - %(asctime)s - %(message)s')

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    console_handler.setFormatter(simple_formatter)
    logger.addHandler(console_handler)

    if BASE_LOG_FILE_PATH:
        current_date = datetime.now().strftime('%Y-%m-%d')

        # Generate log file name with current date
        log_file_name = f"{BASE_LOG_FILE_PATH}log-{current_date}.log"

        file_handler = RotatingFileHandler(log_file_name, maxBytes=1024*1024*5, backupCount=5)
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(verbose_formatter)

        logger.addHandler(file_handler)

    return logger
