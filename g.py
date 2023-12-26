import asyncio
import json
import random

async def send_data(writer):
    try:
        while True:
            data = {
                "bu": "CYGG",
                "from": "PC",
                "version": "V6.0.0",
                "uri": "hq",
                "uid": random.randint(1, 10000),
                "body": "getHq"
            }
            data_str = json.dumps(data)  # 转换为JSON格式的字符串

            # 一个字节一个字节地发送数据
            for byte in (data_str + '\n').encode('utf-8'):
                writer.write(bytes([byte]))
                await writer.drain()
            await asyncio.sleep(1)  # 每秒发送一次
    except ConnectionResetError:
        print("Connection reset by peer")
    except Exception as e:
        print(f"Unexpected error in send_data: {e}")

async def receive_data(reader):
    try:
        while True:
            data = await reader.read(10)  # 一个字节一个字节地接收数据
            if not data:
                print("Connection closed by server")
                break
            print(data)
    except ConnectionResetError:
        print("Connection reset by peer")
    except Exception as e:
        print(f"Unexpected error in receive_data: {e}")

async def main():
    try:
        reader, writer = await asyncio.open_connection('localhost', 8000)
        send_coroutine = send_data(writer)
        receive_coroutine = receive_data(reader)
        await asyncio.gather(send_coroutine, receive_coroutine)
    except ConnectionRefusedError:
        print("Cannot connect to server")
    except Exception as e:
        print(f"Unexpected error in main: {e}")

# 运行异步函数
asyncio.run(main())
