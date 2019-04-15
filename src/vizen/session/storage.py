from typing import Any
from abc import ABC, abstractmethod
from enum import Enum


class SessionLock(Enum):
    READ = 1
    WRITE = 2


class SessionStorage(ABC):
    @abstractmethod
    async def lock(self, id: bytes, mode: SessionLock) -> None:
        pass

    @abstractmethod
    async def release(self, id: bytes, mode: SessionLock) -> None:
        pass

    @abstractmethod
    async def commit(self, id: bytes) -> None:
        pass

    @abstractmethod
    def get(self, key: str) -> Any:
        pass

    @abstractmethod
    def set(self, key: str, value: Any):
        pass

    @abstractmethod
    def delete(self, key: str):
        pass
