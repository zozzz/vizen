from yapic.di import Injector
from .protocol import Request


def fck(i: Injector, r: Request):
    print("fck request", Request, i, r)
    print("fck request 2", i[Request])


class Host:
    @classmethod
    def determine(cls, i: Injector, req: Request) -> "Host":
        # headers = req.headers
        print("determine", Request, i, req)
        print("XXX", i[Request])
        print("XXX", i[Request])
        print("XXX", i[Request])
        print("XXX", i[Request])
        i.exec(fck)
        return Host("fuck.you")
        # headers = req.headers

        # try:
        #     return cls(headers[b"x-forwarded-host"])
        # except KeyError:
        #     return cls(headers[b"host"])

    value: str

    def __init__(self, value):
        if isinstance(value, bytes):
            value = value.decode("idna")
        elif __debug__ and not isinstance(value, str):
            raise RuntimeError("Invalid value for host")
        self.value = value

    def __str__(self):
        return self.value

    def __repr__(self):
        return f"<Host {self.value}>"
