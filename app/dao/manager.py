from abc import ABCMeta, abstractmethod


class DatabaseManager(metaclass=ABCMeta):
    @property
    @abstractmethod
    def client(self):
        raise NotImplementedError

    @property
    @abstractmethod
    def db(self):
        raise NotImplementedError

    @abstractmethod
    def connect(self, host: str, port: int, username: str, password: str, db_name: str):
        raise NotImplementedError

    @abstractmethod
    def disconnect(self):
        raise NotImplementedError


class RedisManager(metaclass=ABCMeta):
    def __init__(self) -> None:
        pass
