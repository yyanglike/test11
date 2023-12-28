import asyncio
import base64
import hashlib
import os
import struct
import random
from hashlib import sha1

class WebSocketClient:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.reader = None
        self.writer = None

    async def connect(self):
        self.reader, self.writer = await asyncio.open_connection(self.host, self.port)
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
        await self.writer.drain()

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
        if length <= 125:
            self.writer.write(bytes([0x8A, 0b10000000 | length]) + mask + masked_payload)
        elif length <= 65535:
            self.writer.write(bytes([0x8A, 0b10000000 | 126]) + struct.pack('!H', length) + mask + masked_payload)
        else:
            self.writer.write(bytes([0x8A, 0b10000000 | 127]) + struct.pack('!Q', length) + mask + masked_payload)
        await self.writer.drain()

    async def close(self):
        self.writer.write(bytes([0x88, 0x00]))
        await self.writer.drain()
        self.writer.close()
        await self.writer.wait_closed()

async def main():
    client = WebSocketClient('localhost', 8765)
    await client.connect()

    while True:
        await client.send_text('hello, world!')
        print('Received:', await client.recv_text())

        await asyncio.sleep(1)

asyncio.run(main())
