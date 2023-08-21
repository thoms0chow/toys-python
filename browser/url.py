import os
import socket
import ssl
from typing import Dict, Tuple


class URL:
    def __init__(self, url: str | None) -> None:
        # Default page
        if not url:
            url = f"file://{os.path.abspath('./tests/default.html')}"

        self.scheme, url = url.split("://", 1)
        assert self.scheme in ["http", "https", "file"], f"Unknown scheme {self.scheme}"

        if self.scheme == "file":
            self.path = url
            self.port = None
            self.host = None
            return

        if "/" not in url:
            url = url + "/"

        self.host, url = url.split("/", 1)
        self.path = "/" + url

        match self.scheme:
            case "http":
                self.port = 80
            case "https":
                self.port = 443

        # Custom port
        if ":" in self.host:
            self.host, port = self.host.split(":", 1)
            self.port = int(port)

    def request(self) -> Tuple[Dict[str, str] | None, str]:
        # File
        if self.scheme == "file":
            if self.path == "/":
                self.path = os.path.abspath("./tests/default.html")
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    body = f.read()
                    return None, body
            except FileNotFoundError:
                return None, "File Not Found"

        # HTTP & HTTPS
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, proto=socket.IPPROTO_TCP)
        if self.scheme == "https":
            ctx = ssl.create_default_context()
            s = ctx.wrap_socket(s, server_hostname=self.host)

        s.connect((self.host, self.port))

        msg = f"GET {self.path} HTTP/1.0\r\nHost: {self.host}\r\n\r\n"
        s.send(msg.encode("utf8"))
        res = s.makefile("r", encoding="utf8", newline="\r\n")

        status_line = res.readline()
        version, status, explanation = status_line.split(" ", 2)
        assert status == "200", f"{status, explanation}"

        headers = {}
        while True:
            line = res.readline()
            if line == "\r\n":
                break
            header, value = line.split(":", 1)
            headers[header.lower()] = value.strip()

        assert "transfer-encoding" not in headers
        assert "content-encoding" not in headers

        body = res.read()
        s.close()

        return headers, body


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

    url = None
    if len(sys.argv) > 1:
        url = sys.argv[1]
    load(URL(url))
