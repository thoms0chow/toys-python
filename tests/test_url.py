import os
from typing import Callable

from _pytest.capture import capsys
import pytest

from browser.url import URL, load, show, transform

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


@pytest.mark.parametrize(
    "url, expected_output",
    [
        ("data:text/html,Hello World!", "Hello World!"),
        ("data:,Hello%2C%20World%21", "Hello, World!"),
        # TODO: MIME type & encoding handling
        # ("data:text/plain;base64,SGVsbG8sIFdvcmxkIQ==", "Hello World!"),
        (
            "data:text/html,%3Ch1%3EHello%2C%20World%21%3C%2Fh1%3E",
            "<h1>Hello, World!</h1>",
        ),
    ],
)
def test_data_url(url: str, expected_output: str) -> None:
    _, response_body = URL(url).request()
    assert response_body == expected_output


def test_compression() -> None:
    url = URL("https://www.google.com", {"Accept-Encoding": "gzip"})
    url.request()


def test_view_source(capsys) -> None:
    # Testcase came from https://github.com/browserengineering/book/discussions/559
    expected_output = "<!doctype><html><head>.*</head><body><p>&lt;html /&gt; is nifty</p></body></html>"
    show(transform(expected_output))

    captured = capsys.readouterr()
    assert expected_output == captured.out.rstrip(
        "\n"
    ), f"View-source mode not respected"
