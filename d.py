import random
import asyncio
import websockets
import json

import logging
logger = logging.getLogger('websockets.protocol')
logger.setLevel(logging.CRITICAL)

# 创建一个事件对象
stop_event = asyncio.Event()

# WebSocket连接地址
url = "ws://192.168.11.42:8000/wss"
url = "ws://127.0.0.1:8000"
# 定义发送数据的函数
async def send_data(ws):
    while True:
        try:
            # 定义要发送的数据
            data = {
                "bu": "CYGG",
                "from": "PC",
                "version": "V6.0.0",
                "uri": "hq",
                "uid": random.randint(1, 10000),
                # "uid": 100,
                "body": "getHq"
            }
            
            data_json = json.dumps(data)  # 转换数据为JSON格式

            # 发送数据
            await ws.send(data_json)
            await asyncio.sleep(0.0001)

            # 不关闭连接，保持连接开放并发送数据
        except Exception as e:
            print("Error:", e)
            # 发生异常时，设置事件
            stop_event.set()
            break  # 发生错误时退出循环

# 定义接收数据的函数
async def receive_data(ws):
    while not stop_event.is_set():  # 检查事件是否被设置
        try:
            # 接收数据
            result = await ws.recv()
            # print("Received: %s" % result)
            await asyncio.sleep(10)
        except Exception as e:
            print("Error:", e)
            break  # 发生错误时退出循环

async def create_connection():
    while True:
        try:
            async with websockets.connect(url) as ws:
                # 创建并启动发送数据的任务
                send_task = asyncio.create_task(send_data(ws))

                # 创建并启动接收数据的任务
                receive_task = asyncio.create_task(receive_data(ws))

                # 等待两个任务都完成
                await asyncio.gather(send_task, receive_task)
        except ConnectionRefusedError :
            print("Connection refused by the server, waiting for 5 seconds before retrying...")
            await asyncio.sleep(5)            
        except websockets.exceptions.ConnectionClosed:
            print("Connection closed, retrying...")
            continue
        except KeyboardInterrupt:
            print("Interrupted by user, exiting...")
            break
        except Exception as e:
            print(f"Unexpected error: {e}")
            break

async def main():
    tasks = []
    for _ in range(2):  # 创建10个连接
        tasks.append(create_connection())
    try:
        await asyncio.gather(*tasks, return_exceptions=True)
    except KeyboardInterrupt:
        # 当 KeyboardInterrupt 异常发生时，取消所有任务
        for task in tasks:
            task.cancel()
        # 等待所有任务完成
        await asyncio.gather(*tasks, return_exceptions=True)

# 运行主函数
asyncio.run(main())