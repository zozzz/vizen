import pickle
from typing import Dict, Tuple, Any
from pathlib import Path
from yapic.di import Inject, Token
from portalocker import RLock, LOCK_EX, LOCK_SH, LOCK_NB

from .storage import SessionStorage, SessionLock, SessionNotFound


class FileSession(SessionStorage):
    __slots__ = ("__path", "__data")

    PATH = Token("PATH")

    __path: Inject[PATH]
    __data: Dict[str, Tuple[RLock, Dict[str, Any]]]

    def __init__(self):
        self.__data = {}

    async def lock(self, id: str, mode: SessionLock) -> None:
        try:
            lock, _ = self.__data[id]
        except KeyError:
            fpath = str(self.__sess_path(id))
            if mode is SessionLock.READ:
                lock = RLock(fpath, mode="rb", flags=LOCK_SH | LOCK_NB)
            else:
                lock = RLock(fpath, mode="r+b", flags=LOCK_EX | LOCK_NB)

        try:
            lock.acquire(10)
        except FileNotFoundError:
            raise SessionNotFound()

        self.__data[id] = (lock, pickle.load(lock.fh))

    async def release(self, id: str, mode: SessionLock) -> None:
        try:
            lock, _ = self.__data[id]
        except KeyError:
            raise RuntimeError("Session is not locked: %r" % id)

        lock.release()
        del self.__data[id]

    async def init(self, id: str, data: dict) -> None:
        pth = self.__sess_path(id)
        if pth.is_file():
            raise RuntimeError("Session already exists")
        else:
            pth.parent.mkdir(0o770, parents=True, exist_ok=True)
            with pth.open("wb") as f:
                pickle.dump(data, f)
            pth.chmod(0o770)

    async def destroy(self, id: str) -> None:
        self.__sess_path(id).unlink()
        try:
            del self.__data[id]
        except KeyError:
            pass

    async def commit(self, id: str) -> None:
        try:
            lock, data = self.__data[id]
        except KeyError:
            raise RuntimeError("Session is not locked: %r" % id)

        lock.fh.seek(0)
        pickle.dump(data, lock.fh)

    async def touch(self, id: str) -> None:
        Path

    def data(self, id: str) -> dict:
        return self.__data[id][1]

    def __sess_path(self, id: str) -> Path:
        return Path(self.__path) / id
