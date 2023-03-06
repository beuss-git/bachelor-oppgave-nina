"""Main file for our application"""
import os
import logging
from logging.handlers import TimedRotatingFileHandler
from app.formats import Formats


class Logger:
    """A class used for setup of logging"""

    # filename for log
    filename = "logfile.log"
    # Set up logging
    # format the log entries
    formatter = logging.Formatter(
        "%(asctime)s %(name)s %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
    )

    def make_handler(self) -> TimedRotatingFileHandler:
        """Set up logging to file to rotate every midnight and set formatter

        Returns:
            _type_: _description_
        """
        handler = TimedRotatingFileHandler(
            f"{Formats.log_path}/{self.filename}",
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
        handler.setFormatter(self.formatter)
        return handler

    def connect_console(self) -> None:
        """Set up logging to console"""
        root_logger = logging.getLogger()
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(self.formatter)
        root_logger.addHandler(console_handler)
        self.logger.info("Logger connected to console")

    # log_location = "main"
    def __init__(self) -> None:
        """initializes the logfile"""
        self.logger = logging.getLogger("log")
        self.logger.setLevel(logging.DEBUG)

        # create directory for logfiles
        if not os.path.exists(Formats.log_path):
            os.makedirs(Formats.log_path)

        # Sets midnight rotation for logger
        self.logger.addHandler(self.make_handler())

        # document that logger is initialized
        self.logger.info("Logger initialized")
