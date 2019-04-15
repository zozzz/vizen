from asyncio import Event

from yapic.di import Inject

from .protocol import SOCK_TRANSPORT


class Input:
    __slots__ = ("sock", "readable")

    sock: Inject[SOCK_TRANSPORT]
    readable: Event

    def __init__(self):
        self.readable = Event()
        self.readable.set()

    def pause_reading(self):
        self.sock.pause_reading()
        self.readable.clear()

    def resume_reading(self):
        self.sock.resume_reading()
        self.readable.set()

    async def read(self):
        await self.readable.wait()
