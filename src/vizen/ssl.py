from pathlib import Path
from ssl import SSLContext


class SSLConfig:
    __slots__ = ("keyfile", "certfile", "version", "cert_required", "ca_certs", "ciphers")

    keyfile: Path
    certfile: Path
    ca_certs: Path
    version: int
    cert_required: bool
    ciphers: str

    def __init__(self,
                 *,
                 keyfile: Path,
                 certfile: Path,
                 ca_certs: Path,
                 version: int = 2,
                 cert_required: bool = False,
                 ciphers: str = "TLSv1"):
        self.keyfile = keyfile
        self.certfile = certfile
        self.ca_certs = ca_certs
        self.version = version
        self.cert_required = cert_required
        self.ciphers = ciphers

    def get_context(self) -> SSLContext:
        pass
