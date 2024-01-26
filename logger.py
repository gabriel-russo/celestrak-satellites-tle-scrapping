from logging import basicConfig, getLogger


class Logger:
    def __init__(self):
        self._log_format = "%(levelname)s %(asctime)s - %(message)s"
        basicConfig(filename="scrap.log", level="INFO", format=self._log_format)
        self._logger = getLogger()

    def log(self, message: str):
        self._logger.info(message)
