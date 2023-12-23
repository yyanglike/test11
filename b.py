import random
from time import sleep
import websocket
import json
import threading

# WebSocket连接地址
url = "ws://192.168.11.42:8000/wss"

# 定义发送数据的函数
def send_data(ws):
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
            ws.send(data_json*100)

            # 不关闭连接，保持连接开放并发送数据
        except Exception as e:
            print("Error:", e)
            break  # 发生错误时退出循环

# 定义接收数据的函数
def receive_data(ws):
    while True:
        try:
            # 接收数据
            result = ws.recv()
            print("Received: %s" % result)
            sleep(1000000)
        except Exception as e:
            print("Error:", e)
            break  # 发生错误时退出循环

# 创建WebSocket连接
ws = websocket.create_connection(url)

# 创建并启动发送数据的线程
send_thread = threading.Thread(target=send_data, args=(ws,))
send_thread.start()

# 创建并启动接收数据的线程
receive_thread = threading.Thread(target=receive_data, args=(ws,))
receive_thread.start()

# 等待两个线程都完成
send_thread.join()
receive_thread.join()
