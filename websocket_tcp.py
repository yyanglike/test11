import socket
import base64
import hashlib
import os
import struct
import random
import threading
import time
import re
import threading
from hashlib import sha1

class WebSocketClient:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((host, port))
        self.running = True
        self.write_lock = threading.Lock()

    def handshake(self, path='/'):
        key = base64.b64encode(os.urandom(16)).decode('utf-8')
        handshake = f'GET {path} HTTP/1.1\r\nHost: {self.host}:{self.port}\r\nConnection: Upgrade\r\nUpgrade: websocket\r\nSec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n'
        self.sock.send(handshake.encode('utf-8'))

        # 先接收HTTP响应的头部
        headers = ''
        while True:
            data = self.sock.recv(1).decode('utf-8')
            headers += data
            if headers.endswith('\r\n\r\n'):
                break

        # 解析头部
        headers = self._parse_http_headers(headers)

        # 根据Content-Length接收响应体
        content_length = int(headers.get('Content-Length', 0))
        body = self.sock.recv(content_length).decode('utf-8')

        # 验证Sec-WebSocket-Accept头
        accept = headers.get('Sec-WebSocket-Accept')
        if accept != base64.b64encode(sha1((key + '258EAFA5-E914-47DA-95CA-C5AB0DC85B11').encode()).digest()).decode():
            raise Exception("Invalid Sec-WebSocket-Accept header")


    def _parse_http_headers(self, response):
        headers = {}
        for line in response.split('\r\n')[1:]:
            if line:
                key, value = line.split(': ', 1)
                headers[key] = value
        return headers

    def send_text(self, message):
        if len(message) > 65535:
            raise ValueError("Message too long")

        # 生成一个4字节的掩码
        mask = struct.pack('!I', random.randint(0, 0xffffffff))
        # 对消息进行掩码处理
        masked_message = bytes(b ^ mask[i % 4] for i, b in enumerate(message.encode('utf-8')))

        length = len(masked_message)
        with self.write_lock:
            if length <= 125:
                # 发送数据帧，第二个字节的最高位设置为1，表示使用了掩码
                self.sock.send(bytes([0x81, 0b10000000 | length]) + mask + masked_message)
            elif length <= 65535:
                self.sock.send(bytes([0x81, 0b10000000 | 126]) + struct.pack('!H', length) + mask + masked_message)
            else:
                self.sock.send(bytes([0x81, 0b10000000 | 127]) + struct.pack('!Q', length) + mask + masked_message)

    def recv_text(self):
        return self._recv_frame()

    def close(self):
        try:
            self.running = False
            self.sock.send(bytes([0x88, 0x80, 0x00, 0x00, 0x00, 0x00]))
            fin, opcode, payload = self._recv_frame()
            assert opcode == 0x8
        except socket.error as e:
            print(f"Socket error: {e}")
        except AssertionError:
            print("Unexpected opcode received.")
        finally:
            self.sock.close()

    def send_ping(self, payload=''):
        if len(payload) > 125:
            raise ValueError("Payload too long")
        mask_key = struct.pack('!I', random.randint(0, 0xffffffff))
        masked_payload = bytes([b ^ mask_key[i % 4] for i, b in enumerate(payload.encode('utf-8'))])
        length = len(payload)
        with self.write_lock:
            self.sock.send(bytes([0x89, 0b10000000 | length]) + mask_key + masked_payload)

    def _recv_frame(self):
        while True:
            data = self.sock.recv(2)
            fin = (data[0] & 0b10000000) != 0
            opcode = data[0] & 0b00001111
            mask = (data[1] & 0b10000000) != 0
            length = data[1] & 0b01111111
            if length == 126:
                length = struct.unpack('>H', self.sock.recv(2))[0]
            elif length == 127:
                length = struct.unpack('>Q', self.sock.recv(8))[0]
            if mask:
                mask_key = self.sock.recv(4)
            payload = self.sock.recv(length)
            if mask:
                payload = bytearray([payload[i] ^ mask_key[i % 4] for i in range(length)])

            if opcode == 0x9:  # Ping frame
                self.send_pong(payload)
            elif opcode == 0xA:  # Pong frame
                print('Received pong:', payload.decode('utf-8', 'ignore'))            
            elif opcode == 0x1:  # Text frame
                return payload.decode('utf-8', 'ignore')
            
    def send_pong(self, payload):
        mask = struct.pack('!I', random.randint(0, 0xffffffff))
        masked_payload = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))

        length = len(masked_payload)
        if length <= 125:
            self.sock.send(bytes([0x8A, 0b10000000 | length]) + mask + masked_payload)
        elif length <= 65535:
            self.sock.send(bytes([0x8A, 0b10000000 | 126]) + struct.pack('!H', length) + mask + masked_payload)
        else:
            self.sock.send(bytes([0x8A, 0b10000000 | 127]) + struct.pack('!Q', length) + mask + masked_payload)

def send_messages(client):
    try:
        while client.running:
            client.send_text('hello, world!')
            time.sleep(1)
    except socket.error as e:
        print(f"socket error:{e}")
    except Exception as e:
        print(f"Error in send_messages: {e}")

def recv_messages(client):
    try:
        while client.running:
            message = client.recv_text()
            if message is not None:
                print('Received:', message)
    except socket.error as e:
        print(f"socket error:{e}")                            
    except Exception as e:
        print(f"Error in recv_messages: {e}")

def send_pings(client, interval=10):
    try:
        while client.running:
            client.send_ping('ping')
            time.sleep(interval)
    except socket.error as e:
        print(f"socket error:{e}")
    except Exception as e:
        print(f"Error in send_pings: {e}")

# 使用示例
client = WebSocketClient('localhost', 8765)
client.handshake('/chat')
# 创建并启动发送消息的线程
send_thread = threading.Thread(target=send_messages, args=(client,))
send_thread.start()

# 创建并启动接收消息的线程
recv_thread = threading.Thread(target=recv_messages, args=(client,))
recv_thread.start()

# 创建并启动发送ping的线程
ping_thread = threading.Thread(target=send_pings, args=(client,))
ping_thread.start()

# 等待两个线程结束
send_thread.join()
recv_thread.join()
ping_thread.join()


client.close()
