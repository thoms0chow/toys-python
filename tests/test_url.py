import os
from typing import Callable

import pytest

from browser.url import URL, load

EXAMPLE_ORG_URL = "https://example.org"


@pytest.fixture()
def local_file_body(file_path: str) -> str:
    try:
        with open(file_path, "r", encoding="utf8") as f:
            return f.read()
    except FileNotFoundError:
        return "File Not Found"


@pytest.mark.parametrize(
    "url, file_path",
    [
        (
            f"file://{os.path.abspath('./tests/sample.txt')}",
            os.path.abspath("./tests/sample.txt"),
        ),
        (None, os.path.abspath("./tests/default.html")),
        ("file://dummy/file/path", "file://dummy/file/path"),
    ],
)
def test_local_file_url(url: str | None, local_file_body: Callable[[str], str]) -> None:
    if url is None:
        _, response_body = URL().request()
    else:
        _, response_body = URL(url).request()
    assert response_body == local_file_body


def test_custom_http_header() -> None:
    headers = {"User-Agent": "Test Toy Browser"}
    url = URL(EXAMPLE_ORG_URL, headers)
    assert set(headers.items()).issubset(
        set(url.headers.items())
    ), "Custom headers is not set"
