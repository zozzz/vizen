from abc import ABC, abstractmethod
from socket import SocketType
from asyncio import AbstractEventLoop

from yapic.di import Inject, Injector, Token

SOCK_LISTEN = Token("SOCK_LISTEN")
SOCK_TRANSPORT = Token("SOCK_TRANSPORT")


class AbstractProtocol(ABC):
    __slots__ = ("injector", "loop")

    injector: Inject[Injector]
    loop: Inject[AbstractEventLoop]

    @abstractmethod
    def connection_lost(self, exc):
        pass

    @abstractmethod
    def pause_writing(self):
        pass

    @abstractmethod
    def resume_writing(self):
        pass

    @abstractmethod
    def data_received(self, data):
        pass

    @abstractmethod
    def eof_received(self):
        pass

    # async def __call__(self):
    #     # await self.request.on_headers.wait()
    #     await self.request.on_body.wait()
