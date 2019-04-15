from yapic.di import Injector
from .protocol import Request

_IS_SECURE = (
    (b"x-forwarded-proto", b"https"),
    (b"x-forwarded-protocol", b"https"),
    (b"front-end-https", b"on"),
    (b"x-forwarded-ssl", b"on"),
    (b"x-url-scheme", b"https"),
)


class Host:
    __slots__ = ("is_secure", "protocol", "domain", "port")

    @classmethod
    def determine(cls, i: Injector, req: Request) -> "Host":
        headers = req.headers

        try:
            host = headers[b"x-forwarded-host"]
        except KeyError:
            host = headers[b"host"]

        for header, value in _IS_SECURE:
            try:
                is_secure = headers[header] == value
                break
            except KeyError:
                is_secure = False

        return Host(host, is_secure)

    is_secure: bool
    protocol: str
    domain: str
    port: int

    def __init__(self, value, is_secure):
        if isinstance(value, bytes):
            value = value.decode("idna")
        elif __debug__ and not isinstance(value, str):
            raise RuntimeError("Invalid value for host")

        idx = value.rfind(":")
        if idx > -1:
            self.domain = value[0:idx]
            self.port = int(value[idx + 1:])
        else:
            self.domain = value
            self.port = None

        self.is_secure = is_secure
        self.protocol = "https" if is_secure else "http"

    def __str__(self):
        return self.domain

    def __repr__(self):
        return f"<Host {self.protocol}://{self.domain}:{self.port}>"
