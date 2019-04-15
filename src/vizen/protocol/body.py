from cgi import parse_header
from http.client import parse_headers
from abc import ABC, abstractmethod
from enum import Enum
from tempfile import TemporaryFile
from io import BytesIO
from typing import List

from ..error import HTTPError


class BodyParser(ABC):
    @abstractmethod
    def feed(self, data: bytes) -> None:
        pass

    @abstractmethod
    def process(self) -> None:
        pass


class FDE_State(Enum):
    EMPTY = 0
    BOUNDARY_RECVD = 1
    HEADERS_RECVD = 2
    CONTENT_RECVD = 4


class FormDataEntry:
    __slots__ = ("headers", "content", "name")

    def __init__(self, headers, content, name):
        self.headers = headers
        self.content = content
        self.name = name


class FormDataFile(FormDataEntry):
    __slots__ = ("filename", "content_type")

    def __init__(self, headers, content, name, filename, content_type):
        FormDataEntry.__init__(self, headers, content, name)
        self.filename = filename
        self.content_type = content_type


# class FormDataParser(BodyParser):
#     __slots__ = ("begin", "end", "buffer", "entries", "current", "parser")

#     begin: bytes
#     buffer: bytes
#     entries: List[FormDataEntry]
#     current: FormDataEntry

#     def __init__(self, boundary: str):
#         self.begin = b"--" + boundary.encode("ASCII")
#         self.end = b"--" + boundary.encode("ASCII") + b"--"
#         self.buffer = b""
#         self.current = FormDataEntry()
#         self.entries = [self.current]
#         self.parser = HttpRequestParser(self)
#         self.parser.feed_data(b"GET / HTTP/1.1\r\n")

#     def feed(self, data: bytes) -> None:
#         self.buffer += data

#         boundary_length = len(self.begin)
#         if len(self.buffer) < boundary_length + 4:
#             # wait for more data
#             return

#         if self.current.state == FDE_State.EMPTY:
#             if not self.buffer.startswith(self.begin):
#                 raise HTTPError(400)
#             else:
#                 self.current.state = FDE_State.BOUNDARY_RECVD
#                 self.buffer = self.buffer[boundary_length + 2:]
#         else:
#             try:
#                 idx = self.buffer.index(self.begin)
#             except ValueError:
#                 pass
#             else:
#                 print("### end found", idx)

#                 self.parser.feed_data(self.buffer[0:idx])

#                 # reset parser
#                 self.parser = HttpRequestParser(self)
#                 self.parser.feed_data(b"GET / HTTP/1.1\r\n")
#                 rem = self.buffer[idx + 1:]
#                 self.buffer = b""
#                 self.feed(rem)
#                 return

#         self.parser.feed_data(self.buffer)

#     def on_header(self, name: bytes, value: bytes) -> None:
#         self.current.headers[name] = value

#     def on_headers_complete(self) -> None:
#         print(self.current.headers)
#         try:
#             cd = self.current.headers[b"content-disposition"]
#         except KeyError:
#             pass
#         else:
#             cd = parse_header(cd.decode("utf-8"))
#             print("content-disposition", cd)

#             self.current.content = TemporaryFile()

#     def on_body(self, body: bytes):
#         pass

#     def begin_entry(self):
#         self.current = FormDataEntry()
#         self.entries.append(self.current)


class FormDataParser(BodyParser):
    __slots__ = ("buffer", "boundary", "fields")

    buffer: bytes
    boundary: bytes
    fields: List[FormDataEntry]

    def __init__(self, boundary: bytes):
        self.buffer = b""
        self.boundary = boundary
        self.fields = []

    def feed(self, data: bytes):
        self.buffer += data

    def process(self):
        if self.buffer is None:
            return

        end = b"--" + self.boundary + b"--\r\n"
        if not self.buffer.endswith(end):
            raise HTTPError(400)

        parts = self.buffer[0:-len(end)].split(b"--" + self.boundary + b"\r\n")
        self.buffer = None

        for part in parts:
            part = part[0:-2]  # remove trailing \r\n
            if not part:
                continue

            sub_parts = part.split(b"\r\n\r\n")
            if len(sub_parts) < 2:
                raise HTTPError(400)

            head = sub_parts.pop(0)
            body = b"\r\n\r\n".join(sub_parts)

            headers = parse_headers(BytesIO(head))

            try:
                cd = headers["content-disposition"]
            except KeyError:
                raise HTTPError(400)
            else:
                cd = parse_header(cd)

                if cd[0] != "form-data":
                    continue

                cd = cd[1]
                if "name" in cd:
                    if "filename" in cd:
                        content = TemporaryFile("wb")
                        content.write(body)

                        if "content-type" in headers:
                            ct = parse_header(headers["content-type"])
                        else:
                            ct = None

                        self.fields.append(FormDataFile(headers, content, cd["name"], cd["filename"], ct))
                    else:
                        self.fields.append(FormDataEntry(headers, body, cd["name"]))


class RawBody(BodyParser):
    __slots__ = ("data", )

    def __init__(self):
        self.data = b""

    def feed(self, data: bytes) -> None:
        self.data += data

    def process(self):
        pass
