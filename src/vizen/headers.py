from typing import Union, Dict

KEY_CACHE: Dict[Union[str, bytes], bytes] = {}


class Headers(dict):
    def __setitem__(self, name: Union[str, bytes], value: bytes) -> None:
        super().__setitem__(self.__key(name), value)

    def __getitem__(self, name: Union[str, bytes]) -> bytes:
        return super().__getitem__(self.__key(name))

    def __delitem__(self, name: Union[str, bytes]) -> None:
        super().__delitem__(self.__key(name))

    def __contains__(self, name):
        return super().__contains__(self.__key(name))

    def __key(self, name: Union[str, bytes]) -> bytes:
        try:
            return KEY_CACHE[name]
        except KeyError:
            if isinstance(name, bytes):
                KEY_CACHE[name] = name.lower()
            elif isinstance(name, str):
                KEY_CACHE[name] = name.encode().lower()
            else:
                raise TypeError("Invalid header name: %r" % name)
        return KEY_CACHE[name]
