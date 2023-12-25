import socket
import random
import json
import threading

import time

def send_data(sock):
    while True:
        try:
            # 发送一个数据帧
            data = {
                "bu": "CYGG",
                "from": "PC",
                "version": "V6.0.0",
                "uri": "hq",
                "uid": random.randint(1, 10000),
                "body": "getHq"
            }
            data_str = json.dumps(data)  # 转换为JSON格式的字符串
            data_bytes = data_str.encode()  # 转换为字节串
            send_websocket_frame(sock, 0x02, data_bytes)

            # 等待一段时间再发送下一帧
            time.sleep(1)
        except socket.error as e:
            print("Socket error:", e)
            break  # 如果发生网络错误，退出循环
        except Exception as e:
            print("Unexpected error:", e)
            break  # 如果发生其他错误，退出循环

def receive_data(sock):
    while True:
        try:
            # 接收一个数据帧
            header = b""
            while len(header) < 8:
                more_header = sock.recv(8 - len(header))
                if not more_header:
                    # 服务器已经关闭了连接
                    return
                header += more_header
            frame_type = header[1]
            data_len = header[2] << 8 | header[3]
            data = b""
            while len(data) < data_len:
                more_data = sock.recv(data_len - len(data))
                if not more_data:
                    # 服务器已经关闭了连接
                    return
                data += more_data

            print(frame_type, data)
        except socket.error as e:
            print("Socket error:", e)
            break  # 如果发生网络错误，退出循环
        except Exception as e:
            print("Unexpected error:", e)
            break  # 如果发生其他错误，退出循环

def send_websocket_frame(sock, frame_type, data):
    data_bytes = data.encode()  # 转换为字节串
    header = bytearray(8)
    header[0] = 0x00
    header[1] = frame_type
    header[2] = len(data_bytes) >> 8
    header[3] = len(data_bytes) & 0xFF
    sock.sendall(header)
    sock.sendall(data_bytes)
            

# def send_websocket_frame(sock, frame_type, data):
#     header = bytearray(8)
#     header[0] = 0x00
#     header[1] = frame_type
#     header[2] = len(data) >> 8
#     header[3] = len(data) & 0xFF
#     sock.sendall(header)
#     sock.sendall(data)

def main():
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(("localhost", 8000))
        
        handshake_request = (
            "GET /chat HTTP/1.1\r\n"
            "Host: localhost:8000\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            "Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==\r\n"
            "Sec-WebSocket-Version: 13\r\n"
            "\r\n"  # 请求头结束后需要一个额外的换行符
        )
        sock.sendall(handshake_request.encode())


        # 发送一个握手帧
        # send_websocket_frame(sock, 0x01, b"Upgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==\r\nSec-WebSocket-Version: 13\r\n")

        # 创建并启动发送数据的线程
        send_thread = threading.Thread(target=send_data, args=(sock,))
        send_thread.start()

        # 创建并启动接收数据的线程
        receive_thread = threading.Thread(target=receive_data, args=(sock,))
        receive_thread.start()

        # 等待两个线程完成
        send_thread.join()
        receive_thread.join()
    except socket.error as e:
        print("Socket error:", e)
    except KeyboardInterrupt:
        print("Program terminated by user.")
    except Exception as e:
        print("Unexpected error:", e)


if __name__ == "__main__":
    main()