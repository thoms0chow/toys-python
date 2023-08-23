from enum import Enum
import mimetypes
import os
import socket
import ssl
from typing import Dict, Optional, Tuple
import urllib.parse

DEFAULT_PAGE_URL = f"file://{os.path.abspath('./tests/default.html')}"


class Scheme(Enum):
    HTTP = "http"
    HTTPS = "https"
    FILE = "file"
    DATA = "data"


class URL:
    def __init__(
        self, url: str = DEFAULT_PAGE_URL, headers: Optional[Dict[str, str]] = None
    ) -> None:
        self._set_scheme(url)
        self._parse_url(url)

        if self.scheme in [Scheme.HTTP, Scheme.HTTPS]:
            self.headers = {
                "User-Agent": "Toy Browser (In Python)",
                "Host": self.host,
                "Connection": "close",
            }
            if headers is not None:
                self.headers.update(headers)

    def _set_scheme(self, url: str) -> None:
        scheme_str, _ = url.split(":", 1)
        self.scheme = Scheme(scheme_str)
        assert self.scheme in Scheme, f"Unknown scheme {self.scheme}"

    def _parse_url(self, url: str) -> None:
        match self.scheme:
            case Scheme.DATA:
                _, url = url.split(":", 1)
                self.mime_type, self.data = url.split(",", 1)
            case Scheme.FILE:
                _, url = url.split("://", 1)
                self.path = url
            case Scheme.HTTP | Scheme.HTTPS:
                _, url = url.split("://", 1)

                if "/" not in url:
                    url = url + "/"

                self.host, url = url.split("/", 1)
                self.path = "/" + url

                if self.scheme == Scheme.HTTP:
                    self.port = 80
                else:
                    self.port = 443

                # Custom port
                if ":" in self.host:
                    self.host, port = self.host.split(":", 1)
                    self.port = int(port)

    def set_header(self, headers: Dict[str, str]) -> None:
        assert self.scheme in [
            Scheme.HTTP,
            Scheme.HTTPS,
        ], "Header setting only allowed in HTTP/HTTPS request"
        self.headers.update(headers)

    def request(self) -> Tuple[Dict[str, str] | None, str]:
        # File
        if self.scheme == Scheme.FILE:
            if self.path == "/":
                self.path = os.path.abspath("./tests/default.html")
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    body = f.read()
                    return None, body
            except FileNotFoundError:
                return None, "File Not Found"

        # Data
        if self.scheme == Scheme.DATA:
            # TODO: MIME type & encoding handling
            self.data = urllib.parse.unquote(self.data)
            return None, self.data

        # HTTP & HTTPS
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, proto=socket.IPPROTO_TCP)
        if self.scheme == Scheme.HTTPS:
            ctx = ssl.create_default_context()
            s = ctx.wrap_socket(s, server_hostname=self.host)

        s.connect((self.host, self.port))

        msg = f"GET {self.path} HTTP/1.1\r\n"
        for header, value in self.headers.items():
            msg += f"{header}: {value}\r\n"
        msg += "\r\n"
        # msg = f"GET {self.path} HTTP/1.0\r\nHost: {self.host}\r\n\r\n"
        s.send(msg.encode("utf8"))
        res = s.makefile("r", encoding="utf8", newline="\r\n")

        status_line = res.readline()
        version, status, explanation = status_line.split(" ", 2)
        assert status == "200", f"{status, explanation}"

        response_headers = {}
        while True:
            line = res.readline()
            if line == "\r\n":
                break
            response_header, value = line.split(":", 1)
            response_headers[response_header.lower()] = value.strip()

        assert "transfer-encoding" not in response_headers
        assert "content-encoding" not in response_headers

        body = res.read()
        s.close()

        return response_headers, body


def show(body: str) -> None:
    in_angle = False
    for c in body:
        if c == "<":
            in_angle = True
        elif c == ">":
            in_angle = False
        elif not in_angle:
            print(c, end="")


def load(url: URL) -> None:
    headers, body = url.request()
    show(body)


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        load(URL(sys.argv[1]))
    else:
        load(URL())
