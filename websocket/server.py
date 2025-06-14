import asyncio
import json
import websockets
# from lerobot.common.robots.so101_follower import SO101Follower, SO101FollowerConfig

# config = SO101FollowerConfig(
#     port="/dev/ttyACM0",
#     id="robot",
# )
# follower = SO101Follower(config)
# follower.connect()



def comunicacaoRobo():
    pass
    



isleftClick = True
isRightClick = False

def jsonInterpreter(data):
    if data["type"] == "mouseup":
        pass
    elif data["type"] == "mousedown":
        pass 
    elif data["type"] == "wheel":
        data["delta"] = data["delta"] / 100
        print("Wheel " + data["delta"])
        pass
    elif data["type"] == "mousemove":
        pass
    else:
        raise ValueError("Unrecognized type")
    
    


async def handler(websocket):
    async for message in websocket:
        data = json.loads(message)
        jsonInterpreter(data)

async def main():
    async with websockets.serve(handler, "172.16.16.55", 6969):
        print("WebSocket server running on ws://127.0.0.1:6969")
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
