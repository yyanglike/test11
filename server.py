import asyncio
import websockets
import json
import time

connections = {}

# 定义一个字典来存储每个连接的上一次发送消息的时间
last_send_time = {}

# 定义发送消息的最小和最大时间间隔
min_interval = 0.001
max_interval = 5000

lock = asyncio.Lock()

async def echo(websocket, path):
    try:
        async for message in websocket:
            try:
                data = json.loads(message)
            except json.JSONDecodeError:
                print("Received message is not valid JSON.")
                continue
            if not isinstance(data, dict):
                print("Received message is not a dictionary.")
                continue
            # 查找websocket在connections中对应的uid
            uid = next((key for key, value in connections.items() if value == websocket), None)
            if uid is None:
                # 如果在connections中找不到websocket，就使用data中的uid
                uid = data.get('uid')
                connections[uid] = websocket

            last_send_time[uid] = time.time()
            
                # 创建一个副本
            connections_values = list(connections.values())
            for conn in connections_values:
                if conn != websocket:
                    try:
                        await asyncio.wait_for(conn.send(message), timeout=5)
                    except asyncio.TimeoutError:
                        print(f"Closing connection with uid {uid} due to send timeout.")
                        await conn.close()
                        # 在修改字典之前获取锁
                        async with lock:
                            if uid in connections:
                                del connections[uid]
                                del last_send_time[uid]

    except websockets.exceptions.ConnectionClosed:
        print("Connection with client unexpectedly closed.")
    finally:
        # Find the uid for the closed connection and remove it
        uid_to_remove = [uid for uid, conn in connections.items() if conn == websocket]
        if uid_to_remove:
            del connections[uid_to_remove[0]]
            del last_send_time[uid_to_remove[0]]


async def check_send_interval():
    while True:
        current_time = time.time()
        uids_to_remove = []
        for uid, last_time in last_send_time.items():
            # 转化成毫秒。
            interval = (current_time - last_time)*1000      
            if interval < min_interval or interval > max_interval:
                print(f"Closing connection with uid {uid} due to abnormal send interval: {interval} seconds.")
                try:
                    await connections[uid].close()
                except KeyError:
                    print(f"No connection found with uid {uid}.")
                uids_to_remove.append(uid)
        async with lock:
            for uid in uids_to_remove:
                del connections[uid]
                del last_send_time[uid]
        await asyncio.sleep(2)

try:
    start_server = websockets.serve(echo, "localhost", 8000)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(start_server)
    loop.create_task(check_send_interval())
    loop.run_forever()
except KeyboardInterrupt:
    print("Server stopped by user.")
    # Add any cleanup code here
except Exception as e:
    print(f"An error occurred: {e}")
