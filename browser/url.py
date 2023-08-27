"""
Toy Python Browser
    Command: 
        $ python browser/url.py https://www.google.com --headers Accept-Encoding=gzip
"""

import argparse
from enum import Enum
import gzip
import html
import os
import socket
import ssl
from typing import Dict, List, Optional, Tuple
import urllib.parse

DEFAULT_PAGE_URL = f"file://{os.path.abspath('./tests/default.html')}"


class Scheme(Enum):
    HTTP = "http"
    HTTPS = "https"
    FILE = "file"
    DATA = "data"


class URL:
    def __init__(
        self, url: Optional[str] = None, headers: Optional[Dict[str, str]] = None
    ) -> None:
        if url is None:
            url = DEFAULT_PAGE_URL

        # View-source
        self.view_source = True if url.startswith("view-source:") else False
        url = url.strip("view-source:")

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
                self.port = 80 if self.scheme == Scheme.HTTP else 443

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
        s.send(msg.encode("utf8"))
        res = s.makefile("rb", newline="\r\n")

        status_line = res.readline().decode("utf-8")
        version, status, explanation = status_line.split(" ", 2)
        assert status == "200", f"{status, explanation}"

        response_headers: Dict[str, str] = {}
        while True:
            line = res.readline()
            if line == b"\r\n":
                break

            response_header, value = line.decode("utf-8").split(":", 1)
            response_headers[response_header.lower()] = value.strip()

        if (
            "content-type" in response_headers
            and "charset" in response_headers["content-type"]
        ):
            _, charset = response_headers["content-type"].split("; ", 1)
            _, charset_value = charset.split("=", 1)
            encoding = charset_value.strip().lower()
        else:
            encoding = "utf-8"

        if (
            "transfer-encoding" in response_headers
            and response_headers["transfer-encoding"] == "chunked"
        ):
            body_data = res.read()
            binary_body = b""
            pos = 0
            while pos <= len(body_data):
                chunk_size_len = body_data.find(b"\r\n", pos) - pos
                chunk_size = int(
                    body_data[pos : pos + chunk_size_len].decode(encoding), 16
                )
                if chunk_size == 0:
                    break
                pos += chunk_size_len + len("\r\n")
                chunk = body_data[pos : pos + chunk_size]

                binary_body += chunk
                pos += chunk_size + len("\r\n")

            if (
                "content-encoding" in response_headers
                and response_headers["content-encoding"] == "gzip"
            ):
                binary_body = gzip.decompress(binary_body)
            # TODO: Other encoding type
            else:
                pass
        else:
            binary_body = res.read()

        body = binary_body.decode(encoding)
        s.close()
        return response_headers, body


def show(body: str) -> None:
    # View source mode
    if body.startswith("&lt;"):
        print(html.unescape(body))
        return

    in_angle = False
    tags: List[str] = []
    tag_name = ""

    in_entity = False
    entity = ""

    for c in body:
        # Tags
        match c:
            case "<":
                in_angle = True
                tag_name = ""  # reset tag_name when encoutering "<"
                continue
            case ">":
                in_angle = False
                if len(tags) > 1 and tag_name == f"/{tags[-1]}":
                    tags.pop()
                else:
                    tags.append(tag_name.split(" ")[0])
                continue
            case _:
                if in_angle:
                    tag_name += c
                    continue

        # Skip characters not inside <body> </body>
        if "body" not in tags:
            continue

        # Entities
        match c:
            case "&":
                in_entity = True
                entity = "&"
                continue
            case ";" | _ if in_entity:
                entity += c
                if c == ";":
                    print(html.unescape(entity), end="")
                    in_entity = False
                continue

        print(c, end="")


def transform(body: str):
    """
    Transform to escaped HTML entity string
    """
    res = ""
    for c in body:
        c = html.escape(c)
        res += c
    return res


def load(url: URL) -> None:
    _, body = url.request()
    if url.view_source:
        show(transform(body))
    else:
        show(body)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Toy Python Browser CLI")
    parser.add_argument("url", nargs="?", default=None)
    parser.add_argument("--headers", nargs="*", type=str)
    args = parser.parse_args()

    headers: Dict[str, str] = {}
    if args.headers:
        for header in args.headers:
            key, value = header.split("=")
            headers[key] = value

    if args.url:
        load(URL(args.url, headers))
    else:
        load(URL(headers=headers))
