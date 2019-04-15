from datetime import datetime
from http.cookies import SimpleCookie
from yapic.di import Inject

from .protocol.request import Request


class Cookie:
    __slots__ = ("request", "__get", "__set")

    request: Inject[Request]

    def __init__(self):
        headers = self.request.headers
        self.__get = SimpleCookie()
        self.__set = SimpleCookie()

        try:
            cookie = headers[b"cookie"]
        except KeyError:
            pass
        else:
            self.__get.load(cookie.encode("ASCII"))

    def set(self,
            key: str,
            value: str,
            *,
            expires: datetime = None,
            path: str = None,
            comment: str = None,
            domain: str = None,
            max_age: int = None,
            secure: bool = None,
            version: str = None,
            httponly: bool = None) -> None:
        self.__set[key] = value
        m = self.__set[key]

        if expires is not None:
            # TODO: format
            m["expires"] = expires

        if path is not None:
            m["path"] = path

        if comment is not None:
            m["comment"] = comment

        if domain is not None:
            m["domain"] = domain

        if max_age is not None:
            m["max-age"] = max_age

        if secure is not None:
            m["secure"] = secure

        if version is not None:
            m["version"] = version

        if httponly is not None:
            m["httponly"] = httponly

    def __getitem__(self, key: str) -> str:
        try:
            return self.__set[key]
        except KeyError:
            return self.__get[key]

    def __delitem__(self, key: str) -> None:
        self.set(key, "", expires=datetime(1970, 1, 1, 0, 0, 0))
