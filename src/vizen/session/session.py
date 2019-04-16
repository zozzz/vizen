import functools
from typing import Generic, TypeVar, Any, ItemsView, Tuple
from uuid import uuid4

from yapic.di import Inject, Token

from ..protocol import Cookie
from .storage import SessionStorage, SessionLock, SessionNotFound

StorageT = TypeVar("StorageT", bound=SessionStorage)

_NOTSET = {}  # type: ignore


class Session(Generic[StorageT]):
    __slots__ = ("storage", "cookie", "cookie_name", "_id")

    COOKIE_NAME = Token("COOKIE_NAME")
    # COOKIE_PATH = Token("COOKIE_PATH")
    # COOKIE_DOMAIN = Token("COOKIE_DOMAIN")

    storage: Inject[StorageT]
    cookie: Inject[Cookie]
    cookie_name: Inject[COOKIE_NAME]

    def __init__(self):
        try:
            self._id = self.cookie.get(self.cookie_name)
        except KeyError:
            self._id = None

    @property
    def id(self) -> str:
        return self._id

    async def regen_id(self) -> str:
        old_id = self._id
        new_id = str(uuid4())

        if old_id is not None:
            async with SessionContext(self, old_id, SessionLock.WRITE) as old_ctx:
                old_data = await old_ctx.data()
                await self.storage.init(new_id, old_data)
                await old_ctx.destroy()
        else:
            await self.storage.init(new_id, {})

        self.cookie.set(self.cookie_name, new_id, httponly=True)
        self._id = new_id
        return new_id

    async def get(self, name: str, default: Any = _NOTSET) -> Any:
        """ Retrive value from session

        example::

            user_id = await sess.get("user_id")

        """
        async with self.read() as data:
            try:
                return data[name]
            except KeyError as e:
                if default is _NOTSET:
                    raise e
                else:
                    return default

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
        return SessionContext(self, self._id, SessionLock.READ)

    def write(self) -> "SessionContext":
        """  Write bounch of values at once

        example::

            async with sess.write() as data:
                if data["user_id"]:
                    user = await User.get(data["user_id"])
                    data["user_role"] = user.role
        """
        return SessionContext(self, self._id, SessionLock.WRITE)


def _lock_req(lt: SessionLock):
    def decor(fn):
        @functools.wraps(fn)
        def wrapper(self, *args, **kwargs):
            if self._locked is False:
                raise RuntimeError("You must lock the session before write values")
            elif self.lock_type is not lt:
                if lt is SessionLock.WRITE:
                    raise RuntimeError("Session is in readonly mode, you must acquire write lock, to write values")
            return fn(self, *args, **kwargs)

        return wrapper

    return decor


class SessionContext:
    __slots__ = ("session", "storage", "id", "lock_type", "_locked")

    session: Session
    storage: SessionStorage
    id: str
    lock_type: SessionLock
    _locked: bool

    def __init__(self, session: Session, id: str, lock_type: SessionLock):
        self.session = session
        self.storage = session.storage
        self.id = id
        self.lock_type = lock_type
        self._locked = False

    async def __aenter__(self):
        if self.id is None:
            self.id = await self.session.regen_id()

        try:
            await self.storage.lock(self.id, self.lock_type)
        except SessionNotFound:
            self.session._id = None
            self.id = await self.session.regen_id()
            await self.storage.lock(self.id, self.lock_type)

        self._locked = True
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if self.lock_type is SessionLock.WRITE:
            await self.storage.commit(self.id)

        await self.storage.release(self.id, self.lock_type)
        self._locked = False

    @_lock_req(SessionLock.READ)
    def __getitem__(self, key: str) -> Any:
        return self.storage.get(self.id, key)

    @_lock_req(SessionLock.WRITE)
    def __setitem__(self, key: str, value: Any) -> None:
        self.storage.set(self.id, key, value)

    @_lock_req(SessionLock.WRITE)
    def __delitem__(self, key: str) -> None:
        self.storage.delete(self.id, key)

    @_lock_req(SessionLock.READ)
    def __iter__(self) -> ItemsView[str, Any]:
        return self.storage.data(self.id).items()

    @_lock_req(SessionLock.READ)
    def data(self) -> dict:
        if self._locked is False:
            raise RuntimeError("You must lock the session before read values")
        return self.storage.data(self.id)

    @_lock_req(SessionLock.WRITE)
    async def init(self, data: dict) -> None:
        await self.storage.init(self.id, data)

    @_lock_req(SessionLock.WRITE)
    async def destroy(self) -> None:
        await self.storage.destroy(self.id)
