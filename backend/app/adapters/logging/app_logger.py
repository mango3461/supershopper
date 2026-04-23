import logging

from app.ports.logger_port import LoggerPort


class AppLogger(LoggerPort):
    def __init__(self) -> None:
        logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
        self._logger = logging.getLogger("supershopper")

    def debug(self, message: str) -> None:
        self._logger.debug(message)

    def info(self, message: str) -> None:
        self._logger.info(message)

    def warning(self, message: str) -> None:
        self._logger.warning(message)

    def error(self, message: str) -> None:
        self._logger.error(message)

