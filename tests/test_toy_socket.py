import logging
import random
import socket
import threading
import time
from typing import Generator

import pytest

from network.toy_socket import CONCURRENT_NUM, MSG_LEN, ToySocketServer


server_host = "localhost"
server_port = 12000


def send(client_num: int) -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.connect((server_host, server_port))

            sock.send(f"Client of Neo {client_num}".encode())
            sock.recv(MSG_LEN).decode()
        except Exception as e:
            print(e)


def start_server() -> None:
    server = ToySocketServer("", server_port)
    server.serve()


@pytest.fixture(scope="module")
def start() -> Generator:
    server_thread = threading.Thread(target=start_server, args=())
    server_thread.daemon = True
    server_thread.start()
    time.sleep(2)
    yield


def test_socket(start) -> None:
    threads = []

    client_nums = [random.randint(1, 100) for i in range(CONCURRENT_NUM)]

    for client_num in client_nums:
        thread = threading.Thread(target=send, args=(client_num,))
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()

    send(101)
