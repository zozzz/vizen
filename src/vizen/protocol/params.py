from typing import Dict, Union, Any

ParamsDict = Dict[str, Union[str, int, float, list]]

_DEFAULT: Any = dict()


class Params:
    __slots__ = ("__url", "__get", "__post")

    def __init__(self, url: ParamsDict, get: ParamsDict, post: ParamsDict):
        self.__url = url
        self.__get = get
        self.__post = post

    def get(self, key: str, default: Any = _DEFAULT):
        try:
            return self[key]
        except KeyError:
            if default is _DEFAULT:
                raise
            else:
                return default

    def GET(self, key: str, default: Any = _DEFAULT):
        """ Get parameter from only 'GET' parameters

        request.params.GET("name")
        """
        try:
            return self.__get[key]
        except KeyError:
            if default is _DEFAULT:
                raise
            else:
                return default

    def POST(self, key: str, default: Any = _DEFAULT):
        """ Get parameter from only 'POST' parameters

        request.params.POST("name")
        """
        try:
            return self.__post[key]
        except KeyError:
            if default is _DEFAULT:
                raise
            else:
                return default

    def __getitem__(self, key):
        try:
            return self.__url[key]
        except KeyError:
            try:
                return self.__get[key]
            except KeyError:
                try:
                    return self.__post[key]
                except KeyError:
                    raise KeyError("missing request param: %r" % key)

    def __getattr__(self, key):
        return self[key]
