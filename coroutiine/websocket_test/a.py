import socket
import struct

def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('localhost', 12345))
    server_socket.listen(1)
    print("Server is running and waiting for connections...")
    while True:
        client_socket, client_address = server_socket.accept()
        print(f"Accepted connection from {client_address}")
        partial_msg = b""
        while True:
            data = client_socket.recv(1024)
            if not data:
                break
            partial_msg += data
            while len(partial_msg) >= 8: # Check if we have enough data to read the length
                if partial_msg[:4] != b"AAAA":
                    partial_msg = partial_msg[1:] # Skip one byte
                    continue
                msg_len = struct.unpack('I', partial_msg[4:8])[0]
                if len(partial_msg) >= 8 + msg_len: # Check if we have a full message
                    msg = partial_msg[8:8+msg_len]
                    print(f"Received data: {msg}")
                    partial_msg = partial_msg[8+msg_len:] # Remove the message from the buffer
                    # Echo back the received message
                    client_socket.sendall(b"AAAA" + struct.pack('I', len(msg)) + msg)
                else:
                    break
        client_socket.close()
        print(f"Connection with {client_address} closed.")

if __name__ == "__main__":
    start_server()
