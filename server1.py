import asyncio

async def handle_client(reader, writer):
    while True:
        data = await reader.readuntil(b'\n')  # 读取数据，直到遇到换行符
        message = data.decode('utf-8').strip()  # 将字节串解码为字符串，并去掉换行符
        print("Received message:", message)

        # 将消息发送回客户端
        writer.write((message + '\n').encode('utf-8'))
        await writer.drain()

async def main():
    server = await asyncio.start_server(handle_client, 'localhost', 8000)
    async with server:
        await server.serve_forever()

# 运行异步函数
asyncio.run(main())
