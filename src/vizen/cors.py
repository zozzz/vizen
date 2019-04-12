from yapic.di import Inject, Token

from .protocol import Response, Request
from .error import HTTPError

CORS_ORIGINS = Token("CORS_ORIGINS")


def CORS(request: Request, response: Response, origins: CORS_ORIGINS):
    headers = request.headers

    try:
        origin = headers[b"origin"]
    except KeyError:
        response.headers[b"access-control-allow-origin"] = b"*"
    else:
        if origin not in origins:
            raise HTTPError(403)
        else:
            response.headers[b"access-control-allow-origin"] = origin
