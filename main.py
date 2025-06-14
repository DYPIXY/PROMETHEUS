import asyncio
import json
import websockets
import threading
import numpy as np
from lerobot.common.robots.so101_follower import SO101Follower, SO101FollowerConfig
from camera import cameraStream
config = SO101FollowerConfig(
    port="/dev/ttyACM0",
    id="robot",
)
follower = SO101Follower(config)
follower.connect()


#shoulder_pan.pos/shoulder_lift.pos/elbow_flex.pos/wrist_flex.pos/wrist_roll.pos/gripper.pos


VELOCITY = 7
isLeftClick = False
isRightClick = False
isQPressed = False
isEPressed = False

deltaX = 0

async def jsonInterpreter(data):
    global isLeftClick
    global isRightClick
    global isEPressed
    global isQPressed
    global deltaX
    # state = follower.get_observation()
    if data["type"] == "mouseup":
        if data["button"] == 0:
            isLeftClick = False
        elif data["button"] == 2:
            isRightClick = False
    elif data["type"] == "mousedown":
        if data["button"] == 0:
            isLeftClick = True
        elif data["button"] == 2:
            isRightClick = True
    elif data["type"] == "wheel":
        pass
    elif data["type"] == "mousemove":
        deltaX += data["x"] * 1000
        pass
    elif data["type"] == "keydown":
        if data["key"] == "q":
            isQPressed = True
        elif data["key"] == "e":
            isEPressed = True
        
    elif data["type"] == "keyup":
        if data["key"] == "q":
            isQPressed = False
        elif data["key"] == "e":
            isEPressed = False
    else:
        raise ValueError("Unrecognized type")
    
    


async def handler(websocket):
    async for message in websocket:
        data = json.loads(message)
        await jsonInterpreter(data)

def main_robot_loop():
    global follower
    global deltaX
    global isLeftClick
    global isRightClick
    
    while True:
        state = follower.get_observation()
        if isRightClick:
            follower.send_action({"gripper.pos": state["gripper.pos"] + 3})
        if isLeftClick:
            follower.send_action({"gripper.pos": state["gripper.pos"] - 3})
        if isQPressed:
            follower.send_action({"wrist_roll.pos": state["wrist_roll.pos"] + 3})
        if isEPressed:
            follower.send_action({"wrist_roll.pos": state["wrist_roll.pos"] - 3})
        deltaXSign = np.sign(deltaX)
        vel = VELOCITY
        if np.sign(deltaX - vel * deltaXSign) != deltaXSign:
            vel = abs(deltaX)
        deltaX -= vel * deltaXSign
        follower.send_action({"shoulder_pan.pos": state["shoulder_pan.pos"] + vel * deltaXSign})

        



async def serveWebsocket():
    async with websockets.serve(handler, "172.16.19.183", 6969):
        print("WebSocket server running on ws://127.0.0.1:6969")
        await asyncio.Future()


async def main():
    camera_loop = threading.Thread(target=cameraStream)
    camera_loop.start()
    main_read_loop = threading.Thread(target=main_robot_loop)
    main_read_loop.start()
    async with websockets.serve(handler, "172.16.19.183", 6969):
        print("WebSocket server running on ws://127.0.0.1:6969")
        await asyncio.Future()
    




if __name__ == "__main__":
    asyncio.run(main())
