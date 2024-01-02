import asyncio
import websockets
import queue
import time
import concurrent.futures

class Server:
    def __init__(self):
        self.clients = {}
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=5)

    async def handler(self, websocket, path):
        q = asyncio.Queue()
        self.clients[websocket] = q
        send_tasks = [asyncio.create_task(self.send_messages(websocket, q)) for _ in range(2)]
        try:
            while True:
                message = await websocket.recv()
                await self.broadcast(message)
        except websockets.ConnectionClosed:
            pass
        finally:
            for task in send_tasks:
                task.cancel()
            del self.clients[websocket]

    async def send_messages(self, websocket, q):
        count = 0
        send_count = 0
        start_time = time.time()
        print_interval = 5  # print frequency stats every 5 seconds
        while True:
            
            messages_to_send = [await q.get()]
            while len(messages_to_send) < 10 and not q.empty():
                # Get the message from the queue
                message = await q.get()
                # Perform some calculation or processing on the message in a thread pool
                # processed_message = await asyncio.get_running_loop().run_in_executor(self.executor, self.process_message, message)
                # Add the processed message to the list of messages to send
                messages_to_send.append(message)
            await websocket.send("\n".join(messages_to_send))
            count += len(messages_to_send)
            send_count += 1
            if time.time() - start_time >= print_interval:
                print(f"Frequency: {send_count/print_interval} sends/sec, {count/print_interval} messages/sec")
                count = 0
                send_count = 0
                start_time = time.time()

    def process_message(self, message):
        # Perform some calculation or processing on the message
        processed_message = message.upper()
        return processed_message


    async def broadcast(self, message):
        await asyncio.gather(*(q.put(message) for q in self.clients.values()))


server = Server()
start_server = websockets.serve(server.handler, 'localhost', 9000)
asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()












# import asyncio
# import websockets
# import multiprocessing

# import asyncio
# import websockets
# import queue

# class Server:
#     def __init__(self):
#         self.connected = set()
#         self.messages = queue.Queue()
#         self.broadcasting = False

#     async def handler(self, websocket, path):
#         self.connected.add(websocket)
#         try:
#             while True:
#                 message = await websocket.recv()
#                 self.messages.put(message)
#                 if not self.broadcasting:  # 如果当前没有在广播消息，开始新的广播任务
#                     self.broadcasting = True
#                     asyncio.create_task(self.broadcast())
#         except websockets.ConnectionClosed:
#             pass
#         finally:
#             self.connected.remove(websocket)

#     async def send_message(self, ws, message):
#         try:
#             await ws.send(message)
#         except websockets.ConnectionClosed:
#             pass

#     async def broadcast(self):
#         while not self.messages.empty():
#             messages_to_send = []
#             while not self.messages.empty():
#                 messages_to_send.append(self.messages.get())
#             if self.connected and messages_to_send:
#                 message = "\n".join(messages_to_send)  # 合并所有的消息
#                 send_tasks = [self.send_message(ws, message) for ws in self.connected]
#                 await asyncio.gather(*send_tasks)
#             await asyncio.sleep(0.1)  # 等待0.1秒再检查消息队列    
#         self.broadcasting = False  # 广播任务完成



# server = Server()
# start_server = websockets.serve(server.handler, 'localhost', 9000)
# asyncio.get_event_loop().run_until_complete(start_server)
# asyncio.get_event_loop().run_forever()
