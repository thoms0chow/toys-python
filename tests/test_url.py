import os
from typing import Callable

import pytest

from browser.url import URL, load


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
        ("", os.path.abspath("./tests/default.html")),
        ("file://dummy/file/path", "file://dummy/file/path"),
    ],
)
def test_local_file_url(url: str, local_file_body: Callable[[str], str]) -> None:
    _, response_body = URL(url).request()
    assert response_body == local_file_body
