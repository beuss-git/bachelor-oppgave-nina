"""Main file for our application"""
import logging
import os
from logging.handlers import TimedRotatingFileHandler

LOGGER_NAME = "log"
LOG_PATH = "app/log"


def __create_file_handler(
    formatter: logging.Formatter, filename: str
) -> TimedRotatingFileHandler:
    """Set up logging to file to rotate every midnight and set formatter

    Returns:
        _type_: _description_
    """
    handler = TimedRotatingFileHandler(
        f"{LOG_PATH}/{filename}",
        when="midnight",
        backupCount=10,
    )

    # Set up custom naming for log files
    def namer(default_name: str) -> str:
        base_filename, ext, filedate = default_name.split(".")
        return f"{base_filename}.{filedate}.{ext}"

    handler.suffix = "%d-%m-%Y"
    handler.namer = namer
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(formatter)
    return handler


def __create_console_handler(formatter: logging.Formatter) -> logging.Handler:
    """Set up logging to console"""
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    return console_handler


# log_location = "main"
def create_logger(level: int = logging.DEBUG, filename: str = "logfile.log") -> None:
    """Creates a logger with a file handler and a console handler

    Args:
        level: The log level. Defaults to logging.DEBUG.
        filename: The log filename. Defaults to "logfile.log".
    """

    formatter = logging.Formatter(
        "%(asctime)s %(name)s %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
    )
    # Initialize the logger
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(level)

    # create directory for logfiles
    if not os.path.exists(LOG_PATH):
        os.makedirs(LOG_PATH)

    # Sets midnight rotation for logger
    logger.addHandler(__create_file_handler(formatter, filename))

    # Sets console handler for logger
    logger.addHandler(__create_console_handler(formatter))

    # document that logger is initialized
    logger.info("Logger initialized")


def get_logger() -> logging.Logger:
    """Get the logger"""
    return logging.getLogger(LOGGER_NAME)
