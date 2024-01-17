import asyncio
import websockets

connected = set()

async def echo(websocket, path):
    connected.add(websocket)
    try:
        while True:
            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                await asyncio.wait_for(broadcast(message), timeout=1.0)
            except asyncio.TimeoutError:
                print("Receive/Send message timeout, closing connection.")
                break
    finally:
       
        connected.remove(websocket)
        await websocket.close()

async def broadcast(message):
    for ws in connected:
        await ws.send(message)

start_server = websockets.serve(echo, "localhost", 8765)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
