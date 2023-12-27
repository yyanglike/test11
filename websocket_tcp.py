import socket
import base64
import hashlib
import os
import struct
import random
import threading
import time
import re
from hashlib import sha1

class WebSocketClient:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((host, port))
        self.running = True

    def handshake(self, path='/'):
        key = base64.b64encode(os.urandom(16)).decode('utf-8')
        handshake = f'GET {path} HTTP/1.1\r\nHost: {self.host}:{self.port}\r\nConnection: Upgrade\r\nUpgrade: websocket\r\nSec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n'
        self.sock.send(handshake.encode('utf-8'))

        # 接收并解析服务器的响应
        response = self.sock.recv(4096).decode('utf-8')
        headers = self._parse_http_headers(response)

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

    # def send_text(self, message):
    #     if len(message) > 65535:
    #         raise ValueError("Message too long")
    #     mask_key = struct.pack('!I', random.randint(0, 0xffffffff))
    #     masked_message = bytes([b ^ mask_key[i % 4] for i, b in enumerate(message.encode('utf-8'))])
    #     length = len(message)
    #     if length <= 125:
    #         self.sock.send(bytes([0x81, 0b10000000 | length]) + mask_key + masked_message)
    #     elif length <= 65535:
    #         self.sock.send(bytes([0x81, 0b10000000 | 126]) + struct.pack('!H', length) + mask_key + masked_message)
    #     else:
    #         self.sock.send(bytes([0x81, 0b10000000 | 127]) + struct.pack('!Q', length) + mask_key + masked_message)
            
    def send_text(self, message):
        if len(message) > 65535:
            raise ValueError("Message too long")

        # 生成一个4字节的掩码
        mask = struct.pack('!I', random.randint(0, 0xffffffff))
        # 对消息进行掩码处理
        masked_message = bytes(b ^ mask[i % 4] for i, b in enumerate(message.encode('utf-8')))

        length = len(masked_message)
        if length <= 125:
            # 发送数据帧，第二个字节的最高位设置为1，表示使用了掩码
            self.sock.send(bytes([0x81, 0b10000000 | length]) + mask + masked_message)
        elif length <= 65535:
            self.sock.send(bytes([0x81, 0b10000000 | 126]) + struct.pack('!H', length) + mask + masked_message)
        else:
            self.sock.send(bytes([0x81, 0b10000000 | 127]) + struct.pack('!Q', length) + mask + masked_message)
            

    def recv_text(self):
        fin, opcode, payload = self._recv_frame()
        if opcode == 0x1:
            return payload.decode('utf-8', 'ignore')
        return None

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


    def _recv_frame(self):
        while self.running:
            data = self.sock.recv(1)
            if not data:
                raise Exception("Connection closed")
            fin = (ord(data) & 0b10000000) != 0
            opcode = ord(data) & 0b00001111
            if opcode == 0x9:  # Ping frame
                # Send a Pong frame in response
                self.sock.send(bytes([0x8A, 0x00]))
                continue  # Continue to receive the next frame
            elif opcode == 0x88:
                self.close()
                raise Exception("Received close frame")
            data = self.sock.recv(1)
            mask = (ord(data) & 0b10000000) != 0
            length = ord(data) & 0b01111111
            if length == 126:
                length = struct.unpack('>H', self.sock.recv(2))[0]
            elif length == 127:
                length = struct.unpack('>Q', self.sock.recv(8))[0]
            if mask:
                mask_key = self.sock.recv(4)
            payload = self.sock.recv(length)
            if mask:
                payload = bytearray([payload[i] ^ mask_key[i % 4] for i in range(length)])
            return fin, opcode, payload


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

# 使用示例
client = WebSocketClient('localhost', 8765)
client.handshake('/chat')
# 创建并启动发送消息的线程
send_thread = threading.Thread(target=send_messages, args=(client,))
send_thread.start()

# 创建并启动接收消息的线程
recv_thread = threading.Thread(target=recv_messages, args=(client,))
recv_thread.start()

# 等待两个线程结束
send_thread.join()
recv_thread.join()

client.close()
