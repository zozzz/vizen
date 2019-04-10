from asyncio import Event
from yapic.di import Inject

from .protocol import SOCK_TRANSPORT


class Output:
    __slots__ = ("sock", "writable")

    sock: Inject[SOCK_TRANSPORT]
    writable: Event

    def __init__(self):
        self.writable = Event()
        self.writable.set()

    async def write(self, data: bytes):
        await self.writable.wait()
        self.sock.write(data)
