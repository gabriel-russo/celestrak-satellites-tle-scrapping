from logging import getLogger, INFO, StreamHandler, FileHandler, Formatter
from datetime import datetime
from os import getcwd
from os.path import join
from sys import stdout


class SingletonMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]


class Logger(metaclass=SingletonMeta):
    def __init__(self):
        self.logger = None
        self.timers = {}

    def initialize(self, name: str, path: str = getcwd(), filename: str = "script.log"):
        self.logger = getLogger(name)
        self.logger.setLevel(INFO)

        log_format = Formatter(
            fmt="|%(asctime)s| %(levelname)s > %(message)s",
            datefmt="%d/%m %H:%M:%S",
        )

        file_handler = FileHandler(join(path, filename))
        file_handler.setFormatter(log_format)
        self.logger.addHandler(file_handler)

        stdout_handler = StreamHandler(stdout)
        stdout_handler.setFormatter(log_format)
        self.logger.addHandler(stdout_handler)

    def log_info(self, msg: str):
        self.logger.info(msg)

    def log_warning(self, msg: str):
        self.logger.warning(msg)

    def log_error(self, msg: str):
        self.logger.error(msg)

    def start_timer(self, name: str):
        self.timers[name] = datetime.now()

    def end_timer(self, name: str):
        return datetime.now() - self.timers[name]


logger = Logger()
