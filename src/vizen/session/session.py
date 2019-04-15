from typing import Generic, TypeVar, Any

from yapic.di import Inject

from ..protocol import Request, Response
from .storage import SessionStorage, SessionLock

StorageT = TypeVar("StorageT", bound=SessionStorage)


class Session(Generic[StorageT]):
    storage: Inject[StorageT]
    request: Inject[Request]
    response: Inject[Response]

    @property
    def id(self) -> bytes:
        pass

    def regen_id(self) -> bytes:
        pass

    async def get(self, name: str) -> Any:
        """ Retrive value from session

        example::

            user_id = await sess.get("user_id")

        """
        async with self.read() as data:
            return data[name]

    async def set(self, name: str, value: Any) -> None:
        """ Write value to session

        example::

            await sess.set("user_id", 42)

        """
        async with self.write() as data:
            data[name] = value

    def read(self) -> "SessionContext":
        """ Read bounch of session values at once

        example::

            async with sess.read() as data:
                user_id = data["user_id"]
                user_role = data["user_role"]
        """
        return SessionContext(self.storage, self.id, SessionLock.READ)

    def write(self) -> "SessionContext":
        """  Write bounch of values at once

        example::

            async with sess.write() as data:
                if data["user_id"]:
                    user = await User.get(data["user_id"])
                    data["user_role"] = user.role
        """
        return SessionContext(self.storage, self.id, SessionLock.WRITE)


class SessionContext:
    __slots__ = ("storage", "id", "lock_type", "__locked")

    storage: SessionStorage
    id: bytes
    lock_type: SessionLock
    __locked: bool

    def __init__(self, storage: SessionStorage, id: bytes, lock_type: SessionLock):
        self.storage = storage
        self.id = id
        self.lock_type = lock_type
        self.__locked = False

    async def __aenter__(self):
        await self.storage.lock(self.id, self.lock_type)
        self.__locked = True

    async def __aexit__(self, exc_type, exc, tb):
        if self.lock_type is SessionLock.WRITE:
            await self.storage.commit()

        await self.storage.release(self.id, self.lock_type)
        self.__locked = False

    def __getitem__(self, key: str) -> Any:
        if self.__locked is False:
            raise RuntimeError("You must lock the session before read values")
        return self.storage.get(key)

    def __setitem__(self, key: str, value: Any) -> None:
        if self.__locked is False:
            raise RuntimeError("You must lock the session before write values")
        elif self.lock_type is not SessionLock.WRITE:
            raise RuntimeError("Session is in readonly mode, you must require write lock, to write values")
        self.storage.set(key, value)

    def __delitem__(self, key: str) -> None:
        if self.__locked is False:
            raise RuntimeError("You must lock the session before write values")
        elif self.lock_type is not SessionLock.WRITE:
            raise RuntimeError("Session is in readonly mode, you must require write lock, to write values")
        self.storage.delete(key)