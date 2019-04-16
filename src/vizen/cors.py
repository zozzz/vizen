from yapic.di import Inject, Token

from .protocol import Response, Request
from .error import HTTPError


class CORS:
    """ Cross-Origin Resource Sharing

    example::

        @Server.on_options("/cors")
        async def handle_options(cors: CORS):
            cors.allow_methods(b"POST")
            cors.allow_headers(b"content-type")
            cors.max_age(3600)
            await cors.done()

    Function body is not executed if the allowed origins is not contains, the requested origin


    """
    __slots__ = ("request", "response", "origins")

    ALLOWED_ORIGINS = Token("ALLOWED_ORIGINS")

    request: Inject[Request]
    response: Inject[Response]
    origins: Inject[ALLOWED_ORIGINS]

    def __init__(self):
        headers = self.request.headers

        try:
            origin = headers[b"origin"]
        except KeyError:
            self.response.headers[b"access-control-allow-origin"] = b"*"
        else:
            if origin.decode("ASCII") not in self.origins:
                raise HTTPError(403)
            else:
                self.response.headers[b"access-control-allow-origin"] = origin

    def allow_methods(self, *methods: bytes) -> None:
        """ Set ``Access-Control-Allow-Methods`` response header

        example::

            allow_methods(b"GET", b"POST")
        """
        self.response.headers[b"access-control-allow-methods"] = b", ".join(methods)

    def allow_headers(self, *headers: bytes) -> None:
        """ Set ``Access-Control-Allow-Headers`` response header

        example::

            allow_headers(b"content-type", b"origin")
        """
        self.response.headers[b"access-control-allow-headers"] = b", ".join(headers)

    def max_age(self, age: int) -> None:
        """ Set ``Access-Control-Max-Age`` response header

        example::

            max_age(3600)
        """
        self.response.headers[b"access-control-max-age"] = str(age).encode("ASCII")

    async def done(self):
        await self.response.send(b"")
