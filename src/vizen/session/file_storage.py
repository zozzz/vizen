from typing import Any, Dict
from aiofile import AIOFile
from yapic.di import Inject, Token
from os import path, open, name, O_RDONLY, O_RDWR
from portalocker import RLock, LOCK_EX, LOCK_SH, LOCK_NB
import pickle

from .storage import SessionStorage, SessionLock

SESSION_PATH = Token("SESSION_PATH")


class FileSession(SessionStorage):
    __slots__ = ("__files", "__path", "__data")

    __files: Dict[bytes, AIOFile]
    __path: Inject[SESSION_PATH]

    async def lock(self, id: bytes, mode: SessionLock) -> None:
        try:
            lock = self.__files[id]
        except KeyError:
            fpath = path.join(self.__path, id)
            if mode is SessionLock.READ:
                lock = RLock(fpath, mode="r", flags=LOCK_SH | LOCK_NB)
            else:
                lock = RLock(fpath, mode="w", flags=LOCK_EX | LOCK_NB)

            self.__files[id] = lock

        lock.acquire(10)
        self.__data = pickle.load(lock.fh)

    async def release(self, id: bytes, mode: SessionLock) -> None:
        try:
            lock = self.__files[id]
        except KeyError:
            raise RuntimeError("Session is not locked: %r" % id)

        lock.release()

    async def commit(self, id: bytes) -> None:
        try:
            lock = self.__files[id]
        except KeyError:
            raise RuntimeError("Session is not locked: %r" % id)

        pickle.dump(self.__data, lock.fh)

    def get(self, key: str) -> Any:
        return self.__data[key]

    def set(self, key: str, value: Any):
        self.__data[key] = value

    def delete(self, key: str):
        del self.__data[key]
