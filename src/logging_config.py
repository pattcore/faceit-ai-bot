"""
Structured logging configuration
"""

import logging
from datetime import datetime
from pythonjsonlogger import jsonlogger


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter for logs"""

    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        log_record['timestamp'] = datetime.utcnow().isoformat()
        log_record['level'] = record.levelname
        log_record['service'] = 'faceit-ai-bot'


def setup_logging(log_level=logging.INFO):
    """Setup logging configuration"""

    # Root logger
    logger = logging.getLogger()
    logger.setLevel(log_level)

    # Console handler with JSON format
    console_handler = logging.StreamHandler()
    formatter = CustomJsonFormatter(
        '%(timestamp)s %(level)s %(name)s %(message)s'
    )
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler
    file_handler = logging.FileHandler('logs/app.log')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


# Create logger
logger = setup_logging()
