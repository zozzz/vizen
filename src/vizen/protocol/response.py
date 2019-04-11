from typing import Union
from http import HTTPStatus
from yapic.di import Inject, Injector

from ..headers import Headers
from .output import Output

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
        self.headers_sent = False

        # self.output.write = self.transport.write

    async def begin(self,
                    code: int = 200,
                    content_type: bytes = b"text/plain",
                    charset: bytes = b"utf-8",
                    length: int = 0):
        if self.headers_sent is False:
            self.headers_sent = True
            response = (
                _HTTP_STATUS[self.version][code],
                b"\r\n",
                b"content-type: ",
                content_type,
                b"; charset=",
                charset,
                b"\r\n",
                b"content-length: ",
                str(length).encode(),
                b"\r\n",
            )
            await self.output.write(b"".join(response))

            for item in self.headers.items():
                await self.output.write(b": ".join(item) + b"\r\n")

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

    def reset(self):
        self.headers_sent = False
