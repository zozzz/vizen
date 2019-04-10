"""
r = Router()

pattern:
    - /path/{param_name:type/regex}
    - /path/{id:int}
    - /path/{id:float}
    - /path/{id:decimal}
    - /path/{id:uuid}
    - /path/{id:str}
    - /path/{page:int}-{hh:int}.{ext:\\.\\w+}


"""
import re
import uuid
from decimal import Decimal
from typing import Union, Callable, Awaitable, Any, Dict, List, Tuple, Iterable

from yapic.di import Injector, Injectable

from .error import VizenError

RouterHandler = Callable[[Any], Awaitable[Any]]
injector = Injector()


class RouteNotFound(VizenError):
    pass


class RouteGroup:
    """
    rg = RouteGroup()

    @rg.on("url")
    async def handler():
        pass

    @rg.post("url")
    async def handler():
        pass
    """

    routes: Dict[Union[bytes, None], "RouteList"]
    sub_groups: List[Tuple[str, "RouteGroup"]]

    def __init__(self):
        self.routes = {}
        self.sub_groups = []

    def on(self, url: str, *methods: bytes):
        if not methods:
            methods = (b"GET", )

        def wrapper(fn: RouterHandler):
            self.add_handler(methods, url, fn)
            return fn

        return wrapper

    def add_handler(self, methods: Iterable[bytes], url: str, handler: RouterHandler):
        for m in methods:
            self.__add(m, url, handler)

    def add_group(self, prefix: str, group: "RouteGroup"):
        self.sub_groups.append((prefix, group))

    def get(self, url: str):
        return self.__decorator(b"GET", url)

    def head(self, url: str):
        return self.__decorator(b"HEAD", url)

    def post(self, url: str):
        return self.__decorator(b"POST", url)

    def delete(self, url: str):
        return self.__decorator(b"DELETE", url)

    def connect(self, url: str):
        return self.__decorator(b"CONNECT", url)

    def options(self, url: str):
        return self.__decorator(b"OPTIONS", url)

    def trace(self, url: str):
        return self.__decorator(b"TRACE", url)

    def patch(self, url: str):
        return self.__decorator(b"PATCH", url)

    def __add(self, method: bytes, url: str, handler: RouterHandler):
        try:
            container = self.routes[method]
        except KeyError:
            container = self.routes[method] = RouteList()

        route = Route(url, injector.injectable(handler))
        container.add(route)

    def __decorator(self, method: bytes, url: str):
        def wrapper(fn: RouterHandler):
            self.__add(method, url, fn)
            return fn

        return wrapper


class Router(RouteGroup):
    def find(self, url: str, method: bytes) -> Tuple[Injectable, dict]:
        try:
            rl = self.routes[method]
        except KeyError:
            raise RouteNotFound(url)
        else:
            return rl.find(url)


_RE_PARAMS = re.compile(r"\{([^:\s]+)(?:\s*:\s*([^}]+))?\}", re.I)
_RE_TYPE = {
    "float": (r"[+-]?(?:0\.\d|\.\d|[1-9])\d*(?:e\d+)?", float, 10),
    "decimal": (r"[+-]?(?:0\.\d|\.\d|[1-9])\d*(?:e\d+)?", Decimal, 9),
    "int": (r"[+-]?[1-9][0-9]*", int, 8),
    "uuid": (r"[\da-z-]{13}-[1345][\da-z-]{3}-[\da-z-]{17}", uuid.UUID, 7),
    "str": (r".*?", lambda v: v, 7),
    "_all": (r".*?", lambda v: v, 1),
    # todo: date, datetime, time
}

_RE_TYPE["integer"] = _RE_TYPE["int"]
_RE_TYPE["string"] = _RE_TYPE["str"]


class Route:
    __slots__ = ("pattern", "handler", "prefix", "params_regex", "params_conv", "priority")

    pattern: str
    handler: Injectable
    prefix: str
    params_regex: Union[Any, None]
    params_conv: Dict[str, Callable[[str], Any]]
    priority: int

    def __init__(self, pattern: str, handler: Injectable):
        self.params_conv = {}
        self.handler = handler
        self.priority = 0
        pattern = normalize(pattern)

        try:
            params_begin = pattern.index("{")
        except ValueError:
            params_begin = len(pattern)
            self.params_regex = None
        else:
            dynamic = pattern[params_begin:]
            self.params_regex = re.compile("^" + re.sub(_RE_PARAMS, self.__replace_params, dynamic) + "$").match

        self.prefix = pattern[0:params_begin]

    def _handle_match(self, match) -> Dict[str, Any]:
        conv = self.params_conv
        result: Dict[str, Any] = {}
        for k, v in match.groupdict().items():
            result[k] = conv[k](v)
        return result

    def __replace_params(self, match) -> str:
        name, type = match.groups()

        if type is None:
            type = "_all"

        converter: Any = lambda v: v
        re_type: Any

        try:
            re_type, converter, prio = _RE_TYPE[type]
        except KeyError:
            re_type, converter, prio = type, lambda v: v, 20

        self.priority += prio
        self.params_conv[name] = converter

        return "(?P<%s>%s)" % (name, re_type)


class RouteList:
    __slots__ = ("exact", "dynamic")

    exact: Dict[str, Route]
    dynamic: List[Tuple[str, Any, Route]]

    def __init__(self):
        self.exact = {}
        self.dynamic = []

    def add(self, route: Route):
        if route.params_regex:
            self.dynamic.append((route.prefix, route.params_regex, route))
            self.dynamic.sort(key=lambda item: (len(item[0]), item[2].priority), reverse=True)
        else:
            if route.prefix in self.exact:
                raise ValueError("This url is already defined: %r" % route.prefix)
            else:
                self.exact[route.prefix] = route

    def find(self, url: str) -> Tuple[Injectable, dict]:
        url = normalize(url)
        try:
            exact = self.exact[url]
        except KeyError:
            return self.__find_dynamic(url)
        else:
            return (exact.handler, {})

    def __find_dynamic(self, url: str) -> Tuple[Injectable, dict]:
        for prefix, re_params, route in self.dynamic:
            if url.startswith(prefix):
                params = re_params(url[len(prefix):])
                if params:
                    return (route.handler, route._handle_match(params))
        raise RouteNotFound(url)


def normalize(pattern: str) -> str:
    if pattern[0] != "/":
        return f"/{pattern}"
    else:
        return pattern
