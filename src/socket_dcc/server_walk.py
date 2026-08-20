import socket

HOST = "127.0.0.1"
PORT = 5000

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
    server.bind((HOST, PORT))
    server.listen(1)
    print(f"Listening on {HOST}:{PORT}...")

    while True:
        conn, addr = server.accept()
        with conn:
            print("Connected by", addr)
            data = conn.recv(1024)  # receive bytes
            print("Received:", data.decode())

            conn.sendall(b"Message received")