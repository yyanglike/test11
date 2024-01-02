import asyncio
import websockets
from websockets.exceptions import ConnectionClosed

async def send_messages(websocket):
    while True:
        # 发送消息
        await websocket.send("Hello, server!")
        # print("Message sent: Hello, server!")
        # 等待一段时间再发送下一条消息
        await asyncio.sleep(0.0001)

async def receive_messages(websocket):
    while True:
        # 接收消息
        response = await websocket.recv()
        # print(f"Received from server: {response}")
        # await asyncio.sleep(0.0001)  # 加入延迟

async def client():
    uri = "ws://localhost:9000"
    while True:
        try:
            async with websockets.connect(uri) as websocket:
                # 启动发送和接收消息的协程
                send_task = asyncio.create_task(send_messages(websocket))
                receive_task = asyncio.create_task(receive_messages(websocket))
                # 等待两个协程都完成
                await asyncio.gather(send_task, receive_task)
        except ConnectionClosed:
            print("Connection closed, reconnecting...")
            await asyncio.sleep(5)  # 等待一段时间再重新连接

# 运行客户端
asyncio.run(client())
