import abc
import os
from abc import abstractmethod

ENV = os.environ.get("ENVIRONMENT", "test")


class Config(abc.ABC):
    @classmethod
    @abstractmethod
    def get_param(cls, name: str):
        raise NotImplemented()


class EnvConfig(Config):
    @classmethod
    def get_param(cls, name: str) -> str:
        return os.environ.get(name.upper().replace(".", "_").replace("-", "_"))


class Params:
    def __init__(self, config: Config):
        self.DB_USER = config.get_param("DB_USER")
        self.DB_PASSWORD = config.get_param("DB_PASSWORD")
        self.DB_NAME = config.get_param(f"DB_NAME")
        self.DB_ENDPOINT = config.get_param("DB_ENDPOINT")
        self.REDIS_ENDPOINT = config.get_param("REDIS_ENDPOINT")


params = Params(EnvConfig())
