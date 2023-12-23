import random
import asyncio
import websockets
import json

# WebSocket连接地址
url = "ws://192.168.11.42:8000/wss"

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
                "body": "getHq"
            }
            
            data_json = json.dumps(data)  # 转换数据为JSON格式

            # 发送数据
            await ws.send(data_json*100)

            # 不关闭连接，保持连接开放并发送数据
        except Exception as e:
            print("Error:", e)
            break  # 发生错误时退出循环

# 定义接收数据的函数
async def receive_data(ws):
    while True:
        try:
            # 接收数据
            result = await ws.recv()
            print("Received: %s" % result)
            await asyncio.sleep(1000)
        except Exception as e:
            print("Error:", e)
            break  # 发生错误时退出循环

async def main():
    while True:
        try:
            async with websockets.connect(url) as ws:
                # 创建并启动发送数据的任务
                send_task = asyncio.create_task(send_data(ws))

                # 创建并启动接收数据的任务
                receive_task = asyncio.create_task(receive_data(ws))

                # 等待两个任务都完成
                await asyncio.gather(send_task, receive_task)
        except websockets.exceptions.ConnectionClosed:
            print("Connection closed, retrying...")
            continue
        except KeyboardInterrupt:
            print("Interrupted by user, exiting...")
            break
        except Exception as e:
            print(f"Unexpected error: {e}")
            break

# 运行主函数
asyncio.run(main())
