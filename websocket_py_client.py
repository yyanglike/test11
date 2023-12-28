import asyncio
import websockets

async def send_msg(websocket):
    while True:
        await websocket.send("Hello, world!")
        await asyncio.sleep(1)  # 每隔1秒发送一次

async def recv_msg(websocket):
    while True:
        msg = await websocket.recv()
        print(f"Received: {msg}")

async def main():
    uri = "ws://localhost:8765"
    async with websockets.connect(uri) as websocket:
        # 创建并启动两个协程
        task1 = asyncio.create_task(send_msg(websocket))
        task2 = asyncio.create_task(recv_msg(websocket))

        # 等待两个协程结束
        await task1
        await task2

# 运行主协程
asyncio.run(main())
