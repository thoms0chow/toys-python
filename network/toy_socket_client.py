"""Assignment
https://gaia.cs.umass.edu/kurose_ross/programming/simple_socket/
"""
import socket

MSG_LEN = 1024

if __name__ == "__main__":
    server_host = "localhost"
    server_port = 12000

    # Client
    client_num = int(input("Please input a random number between 1 and 100\n"))
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((server_host, server_port))
    client.send(f"Client of Neo {client_num}".encode())
    res = client.recv(MSG_LEN).decode()
    print(res)
    client.close()
