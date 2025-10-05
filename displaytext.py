import asyncio
import websockets
import json

async def send_message():
    uri = "ws://localhost:9000"
    async with websockets.connect(uri) as websocket:
        # Replace 'Your message here' with the text you want to display
        message = {
            "action": "DisplayText",
            "text": "Your message here"
        }
        await websocket.send(json.dumps(message))

asyncio.run(send_message())
