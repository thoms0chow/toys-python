"""Assignment
https://gaia.cs.umass.edu/kurose_ross/programming/simple_socket/
"""
from multiprocessing.pool import ThreadPool
import random
import socket

MSG_LEN = 1024
CONCURRENT_NUM = 10


class ToySocketServer:
    """Socket server"""

    def __init__(self, host: str, port: int) -> None:
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def serve(self) -> None:
        self.sock.bind((self.host, self.port))
        self.sock.listen(CONCURRENT_NUM)
        print("Socket server is ready to receive")

        pool = ThreadPool()

        terminate = False
        while not terminate:
            connection_socket, _ = self.sock.accept()

            terminate = pool.apply_async(server_handler, (connection_socket,)).get()

            if terminate:
                self.sock.close()

            connection_socket.close()


def server_handler(sock: socket.socket) -> bool:
    msg = sock.recv(MSG_LEN).decode()

    msg_arr = msg.split(" ")
    client_name = msg_arr[2:-1][0]
    client_num = int(msg_arr[-1])

    print(f"{client_name}, Neo Server")

    terminate = False
    if client_num >= 1 and client_num <= 100:
        server_num = random.randint(1, 100)
        print(f"{client_num}, {server_num}, {client_num + server_num}")
        res = f"Server of {client_name} {server_num}"
        sock.send(res.encode())
    else:
        terminate = True

    return terminate


if __name__ == "__main__":
    # Server
    server_host = "localhost"
    server_port = 12000

    server = ToySocketServer("", server_port)
    server.serve()
