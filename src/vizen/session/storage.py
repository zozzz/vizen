from typing import Any
from abc import ABC, abstractmethod
from enum import Enum

from ..error import VizenError


class SessionNotFound(VizenError):
    pass


class SessionLock(Enum):
    READ = 1
    WRITE = 2


class SessionStorage(ABC):
    @abstractmethod
    async def lock(self, id: str, mode: SessionLock) -> None:
        pass

    @abstractmethod
    async def release(self, id: str, mode: SessionLock) -> None:
        pass

    @abstractmethod
    async def commit(self, id: str) -> None:
        pass

    @abstractmethod
    async def touch(self, id: str) -> None:
        pass

    @abstractmethod
    async def init(self, id: str, data: dict) -> None:
        pass

    @abstractmethod
    async def destroy(self, id: str) -> None:
        pass

    def get(self, id: str, key: str) -> Any:
        return self.data(id)[key]

    def set(self, id: str, key: str, value: Any):
        self.data(id)[key] = value

    def delete(self, id: str, key: str):
        del self.data(id)[key]

    @abstractmethod
    def data(self, id: str) -> dict:
        pass
