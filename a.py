import random
import websocket
import json
import threading


# WebSocket连接地址
url = "ws://192.168.11.42:8000/wss"

# 定义发送数据的函数
def send_data():

    while True:
        ws = websocket.create_connection(url)

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
            
            # 创建WebSocket连接
            
            data_json = json.dumps(data)  # 转换数据为JSON格式

            # ws = websocket.create_connection(url)

            # 发送数据
            ws.send(data_json)

            # 不关闭连接，保持连接开放并发送数据
        except Exception as e:
            print("Error:", e)
            break  # 发生错误时退出循环

threads = []

for _ in range(1):
    send_thread = threading.Thread(target=send_data)
    send_thread.start()
    threads.append(send_thread)

# 等待所有线程完成
for thread in threads:
    thread.join()
