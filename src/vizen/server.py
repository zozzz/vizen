import socket
import asyncio
from typing import List, Callable, Optional, Any, Tuple, Type, TypeVar, Awaitable
from yapic.di import Injector, Inject

from .ssl import SSLConfig
from .protocol import ProtocolFactory, SOCK_LISTEN
from .event import Event

injector = Injector()

OnInitHandler = Callable[[Injector], None]
OnErrorHandler = Callable[[Any], Awaitable[Any]]

ErrorT = TypeVar("ErrorT", bound=Exception)

_SERVER_INIT: List[OnInitHandler] = []
_SERVER_ERROR: List[Tuple[Type[ErrorT], OnErrorHandler]] = []


class Server:
    __slots__ = ("injector", "loop", "ssl")

    loop: Inject["Loop"]
    ssl: Optional[SSLConfig]

    @classmethod
    def on_init(cls, fn: OnInitHandler) -> None:
        """ Listen application on_init

        example::

            @Server.on_init
            def init_di(injector: Injector) -> None:
                injector.provide(Something)

        """
        _SERVER_INIT.append(injector.injectable(fn))

    @classmethod
    def on_erorr(cls, error: Type[ErrorT]) -> Callable[[OnErrorHandler], OnErrorHandler]:
        """ Listen errors

        example::

            TODO: @Server.on_erorr(HTTPError[300:400])

            @Server.on_erorr(HTTPError)
            def handle_redirect(event: Event, *, error: HTTPError) -> None:
                if 300 <= error.code < 400:
                    event.prevent_default()
                    # ...
        """

        def decorator(fn: OnErrorHandler) -> OnErrorHandler:
            handler = injector.injectable(fn)
            _SERVER_ERROR.insert(0, (error, handler))
            return fn

        return decorator

    @classmethod
    def get(cls, xy):
        def wrap(x):
            pass

        return wrap

    @classmethod
    def start(cls, ip: str, port: int):
        for init in _SERVER_INIT:
            init(injector)

        server = injector.get(cls)
        server.run(ip, port)

    def __init__(self, ssl: SSLConfig = None):
        self.ssl = ssl

    def run(self, ip: str, port: int):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((ip, port))

        self.loop.run_until_complete(self.__run(sock))

    async def __run(self, sock: socket.SocketType):
        await self.serve_from_sock(sock)
        await self.run_forever()

    async def serve_from_fd(self, fd: int):
        return self.serve_from_sock(socket.fromfd(fd, socket.AF_INET, socket.SOCK_STREAM))

    async def serve_from_sock(self, sock: socket.SocketType):
        server_injector = injector.descend()
        server_injector[SOCK_LISTEN] = sock
        # https://docs.python.org/3/library/asyncio-eventloop.html#asyncio.loop.create_server
        try:
            await self.loop.create_server(server_injector[ProtocolFactory], sock=sock)
        except Exception as err:
            handled = await handle_error(server_injector, err)
            if not handled:
                raise

    async def run_forever(self):
        sleep = asyncio.sleep

        while True:
            await sleep(0.1, loop=self.loop)


async def handle_error(injector: Injector, error: Exception) -> bool:
    try:
        exc_injector = injector.descend()

        event = Event()
        exc_injector[Event] = event

        for hexc, hfn in _SERVER_ERROR:
            if isinstance(error, hexc):
                if not event.is_prevented:
                    await hfn(exc_injector)
                else:
                    break

        if event.is_prevented:
            return True
    except Exception:
        # TODO: internal server error
        pass
    else:
        # TODO: default error
        pass

    return False


injector.provide(Server)

from .loop import Loop  # noqa
