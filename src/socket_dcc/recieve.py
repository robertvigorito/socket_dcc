import socket

HOST = "192.168.18.21"
PORT = 5002

code_snippet = """
import runpy

runpy.run_path("//wsl$/Ubuntu/home/robert-v/dev/wgid/socket_dcc/src/socket_dcc/run_py_test.py")

"""

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
    client.connect((HOST, PORT))
    # client.sendall(b"Hello from client")

    # Send a code snippet to the server
    client.sendall(code_snippet.encode("utf-8"))
    # Receive the response from the server
    response = client.recv(4096)
