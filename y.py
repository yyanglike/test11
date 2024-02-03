import websocket
import time
import threading
import json

def on_message(ws, message):
    pass
    # print("Received message: ", str(message))

def on_error(ws, error):
    print("Error: ", str(error))

def on_close(ws, close_status_code, close_msg):
    print("Connection closed.")

def on_open(ws):
    def run(*args):
        while True:
            time.sleep(0.001)
            
            data = {"text": "Hello, server!"}
            ws.send(json.dumps(data))
    thread = threading.Thread(target=run)
    thread.start()

if __name__ == "__main__":
    # websocket.enableTrace(True)
    ws = websocket.WebSocketApp("ws://localhost:8080/ws/test",
                              on_message = on_message,
                              on_error = on_error,
                              on_close = on_close)
    ws.on_open = on_open
    ws.run_forever()
