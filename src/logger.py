from logging import getLogger, INFO, StreamHandler, FileHandler, Formatter, DEBUG
from logging.handlers import SysLogHandler
from os import getcwd
from os.path import join, exists
from sys import stdout
from typing import Optional


class SingletonMeta(type):
    """
    Metaclass singleton.
    """

    __instance = None

    def __call__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = super().__call__(*args, **kwargs)
            return cls.__instance

        return cls.__instance


class Logger(metaclass=SingletonMeta):
    def __init__(self, tag="python"):
        self.__logger = getLogger(tag)
        self.__logger.setLevel(INFO)
        self.__logger.addHandler(StreamHandler(stdout))
        self.__logger.addHandler(SysLogHandler(address="/dev/log"))
        self.__bind_formatter_to_handlers()

    def __bind_formatter_to_handlers(self) -> None:
        for handler in self.__logger.handlers:
            handler.setFormatter(Formatter("%(name)s: [%(levelname)s] %(message)s"))

    def enable_debug_mode(self) -> None:
        self.__logger.setLevel(DEBUG)

    def bind_file(self, filename: str, path: Optional[str] = getcwd()) -> None:
        if filename == "":
            raise Exception("Filename required.")

        if not exists(path):
            raise Exception("Path to folder is not valid.")

        if not filename.endswith(".log"):
            filename += ".log"

        self.__logger.addHandler(FileHandler(join(path, filename)))

        self.__bind_formatter_to_handlers()

    def info(self, msg: str) -> None:
        self.__logger.info(msg)

    def warning(self, msg: str) -> None:
        self.__logger.warning(msg)

    def error(self, msg: str) -> None:
        self.__logger.error(msg)

    def debug(self, msg: str) -> None:
        self.__logger.debug(msg)
