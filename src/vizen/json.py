from typing import Any, Union

try:
    from yapic import json
except ImportError:
    import json  # type: ignore


class Json:
    def dumps(self, obj: Any) -> bytes:
        return json.dumps(obj)

    def loads(self, obj: Union[str, bytes]) -> Any:
        return json.loads(obj)
