import socket
import struct
import json
import time

def send_data(sock, data1):
    # 准备数据
    data = {'user': 'HelloWorld','cmd': 7,'groupId':'yuanda/node/cem'}  # 这是要发送的数据
    data = json.dumps(data)  # 转化为JSON字符串
    data_length = len(data)  # 数据的长度
    

    # 按照你描述的格式打包数据
    # 第一个字节是1，第二个字节是81，第三个字节是7，然后是数据的长度，最后是数据内容
    packet = struct.pack('!BBBI', 1, 81, 7, data_length) + data.encode()

    # 发送数据
    # sock.send(packet)
    # 一个字节一个字节地发送数据
    for byte in packet:
        sock.send(bytes([byte]))
        time.sleep(1)  # 睡眠1秒

def main():
    # 创建一个socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # 连接到服务器
    sock.connect(("8.131.101.60", 8888))

    # 发送数据
    send_data(sock,"Hello, world!")

    # 关闭socket
    sock.close()

main()
