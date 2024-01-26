import asyncio
import base64
import hashlib
import os
import struct
import random
from hashlib import sha1
import socket
from datetime import datetime

class WebSocketClient:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.reader = None
        self.writer = None

    async def connect(self):
        
        # 创建一个自定义的socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # 设置发送和接收缓冲区大小
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1024)  # 1MB
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 1024)  # 1MB

        # 将socket连接到目标地址
        sock.connect(('localhost', 9002))

        # 获取当前的事件循环
        loop = asyncio.get_running_loop()
        # 将socket转换为asyncio的StreamReader和StreamWriter
        self.reader = asyncio.StreamReader()
        protocol = asyncio.StreamReaderProtocol(self.reader)
        transport, _ = await loop.create_connection(lambda: protocol, sock=sock)
        self.writer = asyncio.StreamWriter(transport, protocol, self.reader, loop)      
        # self.reader, self.writer = await asyncio.open_connection(self.host, self.port)
        await self.handshake()

    async def handshake(self, path='/'):
        key = base64.b64encode(os.urandom(16)).decode('utf-8')
        handshake = f'GET {path} HTTP/1.1\r\nHost: {self.host}:{self.port}\r\nConnection: Upgrade\r\nUpgrade: websocket\r\nSec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n'
        self.writer.write(handshake.encode('utf-8'))
        await self.writer.drain()

        headers = await self.reader.readuntil(b'\r\n\r\n')
        headers = self._parse_http_headers(headers.decode('utf-8'))

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

    async def send_text(self, message):
        if len(message) > 65535:
            raise ValueError("Message too long")
    
        mask = struct.pack('!I', random.randint(0, 0xffffffff))
        masked_message = bytes(b ^ mask[i % 4] for i, b in enumerate(message.encode('utf-8')))
    
        length = len(masked_message)
        if length <= 125:
            self.writer.write(bytes([0x81, 0b10000000 | length]) + mask + masked_message)
        elif length <= 65535:
            self.writer.write(bytes([0x81, 0b10000000 | 126]) + struct.pack('!H', length) + mask + masked_message)
        else:
            self.writer.write(bytes([0x81, 0b10000000 | 127]) + struct.pack('!Q', length) + mask + masked_message)
        try:
            await asyncio.wait_for(self.writer.drain(), timeout=10)
        except asyncio.TimeoutError:
            raise TimeoutError("Network write operation timed out")

    async def recv_text(self):
        while True:
            data = await self.reader.readexactly(2)
            fin = (data[0] & 0b10000000) != 0
            opcode = data[0] & 0b00001111
            mask = (data[1] & 0b10000000) != 0
            length = data[1] & 0b01111111
            if length == 126:
                length = struct.unpack('>H', await self.reader.readexactly(2))[0]
            elif length == 127:
                length = struct.unpack('>Q', await self.reader.readexactly(8))[0]
            if mask:
                mask_key = await self.reader.readexactly(4)
            payload = await self.reader.readexactly(length)
            if mask:
                payload = bytearray([payload[i] ^ mask_key[i % 4] for i in range(length)])

            if opcode == 0x9:  # Ping frame
                await self.send_pong(payload)
            elif opcode == 0x1:  # Text frame
                return payload.decode('utf-8', 'ignore')

    async def send_pong(self, payload):
        mask = struct.pack('!I', random.randint(0, 0xffffffff))
        masked_payload = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))
    
        length = len(masked_payload)
        header = [0x8A]
        if length <= 125:
            header.append(0b10000000 | length)
        elif length <= 65535:
            header.append(0b10000000 | 126)
            header.extend(struct.pack('!H', length))
        else:
            header.append(0b10000000 | 127)
            header.extend(struct.pack('!Q', length))
    
        self.writer.write(bytes(header) + mask + masked_payload)
        await self.writer.drain()

    async def close(self):
        self.writer.write(bytes([0x88, 0x00]))
        await self.writer.drain()
        self.writer.close()
        await self.writer.wait_closed()
        
async def send(client, event):
    count = 0
    while not event.is_set():
        try:
            await client.send_text('hello, world!'*100)
            await asyncio.sleep(1)
            count += 1
            if count % 10000 == 0:
                now = datetime.now()
                print(f'{now} Sends:')
        except Exception as e:
            print(f"Error occurred while sending: {e}")
            event.set()
            break


async def recv(client, event):
    count = 0
    while not event.is_set():
        try:
            now = datetime.now()
            text = await client.recv_text()
            count += 1
            if count % 10000 == 0:
                print(f'{now} Received:', text[:5])
            await asyncio.sleep(1)
        except Exception as e:
            print(f"Error occurred while receiving: {e}")
            event.set()
            break

        
async def main():
    client = WebSocketClient('localhost', 9002)
    await client.connect()

    event = asyncio.Event()

    # 创建两个任务
    send_task = asyncio.create_task(send(client, event))
    recv_task = asyncio.create_task(recv(client, event))

    try:
        done, pending = await asyncio.wait([send_task, recv_task], return_when=asyncio.FIRST_EXCEPTION)
    except Exception as e:
        print(f"Error occurred: {e}")
        event.set()

    for task in pending:
        task.cancel()

    # 等待两个任务都完成
    await asyncio.gather(send_task, recv_task)
asyncio.run(main())
