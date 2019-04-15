from typing import Union, Any
from http import HTTPStatus
from yapic.di import Inject, Injector

from ..headers import Headers
from ..json import Json
from .output import Output
from .cookie import Cookie

_HTTP_STATUS = {}

for v in ("1.0", "1.1", "2.0"):
    _HTTP_STATUS[v] = {entry.value: f"HTTP/{v} {entry.value} {entry.phrase}".encode() for entry in HTTPStatus}


class Response:
    __slots__ = ("injector", "headers", "transport", "version", "headers_sent", "output")

    injector: Inject[Injector]
    headers: Headers
    output: Inject[Output]
    version: str
    headers_sent: bool

    def __init__(self):
        self.headers = Headers()
        self.headers[b"content-type"] = b"text/plain; charset=utf-8"
        self.headers_sent = False

        # self.output.write = self.transport.write

    async def begin(self, code: int = 200, length: int = 0):
        if self.headers_sent is False:
            self.headers_sent = True
            response = (
                _HTTP_STATUS[self.version][code],
                b"\r\n",
                b"content-length: ",
                str(length).encode(),
                b"\r\n",
            )
            await self.output.write(b"".join(response))

            for item in self.headers.items():
                await self.output.write(b": ".join(item) + b"\r\n")

            cookies = self.injector[Cookie]
            for c in cookies._new():
                await self.output.write(b"set-cookie: " + c.OutputString().encode("ASCII") + b"\r\n")

            await self.output.write(b"\r\n")
        else:
            raise RuntimeError("Headers already sent")

    async def send(self, data: Union[str, bytes], code: int = 200) -> None:
        if isinstance(data, str):
            data = data.encode()

        await self.begin(code=code, length=len(data))
        await self.output.write(data)
        self.reset()
        # self.output.sock.close()

    def text(self, data: str):
        return self.send(data)

    def html(self, data: str):
        self.headers[b"content-type"] = b"text/html; charset=utf-8"
        return self.send(data)

    def json(self, data: Any):
        self.headers[b"content-type"] = b"application/json; charset=utf-8"
        return self.send(self.injector[Json].dumps(data))

    def reset(self):
        self.headers_sent = False
