from abc import ABC, abstractmethod


class LoggerPort(ABC):
    @abstractmethod
    def debug(self, message: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def info(self, message: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def warning(self, message: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def error(self, message: str) -> None:
        raise NotImplementedError

