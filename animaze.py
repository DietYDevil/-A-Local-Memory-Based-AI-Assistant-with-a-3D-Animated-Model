import websockets
import json
import asyncio


async def animation(action,index, delay=0):
    try:
        await asyncio.sleep(delay)
        
        async with websockets.connect("ws://localhost:9000") as websocket:

            # Send animation command
            command = json.dumps({"action": action,
                                        "index" : index })
            await websocket.send(command)
        
    except Exception as e:
        print(f"Error in animation: {e}")


async def eye_blink(action,behavior,value):
    try:
        async with websockets.connect("ws://localhost:9000") as websocket:
            command = json.dumps({"action" : action,
                                "behavior" : behavior,
                                "value" : value})
            await websocket.send(command)
    except Exception as e:
        print(f"error in eye blink : {e}")

async def dance():
    try:
        print()
        
        
    except Exception as e:
        print(f"sorry sir, i cant dance : {e}")

    
# asyncio.run(eye_blink("SetOverride","Auto Blink",True))
# asyncio.run(animation("TriggerSpecialAction",0))           # hello animation
# asyncio.run(animation("TriggerIdle",17))          # simple standing
# asyncio.run(animation("TriggerSpecialAction",15))    # goodbye animation
# asyncio.run(animation("TriggerIdle",26,delay=5))