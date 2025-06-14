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
initialPos = {'shoulder_pan.pos': 3, 'shoulder_lift.pos': -95, 'elbow_flex.pos': 64, 'wrist_flex.pos': -83, 'wrist_roll.pos': 1, 'gripper.pos': 14}


SCROLL_VEL = 6
VELOCITY = 7
isLeftClick = False
isRightClick = False
isBackButtonClick = False
isForwardButtonClick = False
isQPressed = False
isEPressed = False


async def setInitialPos():
    global state
    global shoulderMeta
    global shoulderLiftMeta
    global elbowFlexMeta
    follower.send_action(initialPos)
    await asyncio.sleep(2)
    # follower.send_t_action({"delta_x": 0.1})
    # await asyncio.sleep(2)

    state = follower.get_observation()
    shoulderMeta = state["shoulder_pan.pos"] 
    shoulderLiftMeta = state["shoulder_lift.pos"]
    elbowFlexMeta = state["elbow_flex.pos"]


async def jsonInterpreter(data):
    global isLeftClick
    global isRightClick
    global isBackButtonClick
    global isForwardButtonClick
    global isEPressed
    global isQPressed
    global shoulderMeta
    global elbowFlexMeta
    global shoulderLiftMeta
    # global follower

    # state = follower.get_observation()
    if data["type"] == "mouseup":
        if data["button"] == 0:
            isLeftClick = False
        elif data["button"] == 2:
            isRightClick = False
        elif data["button"] == 3:
            isBackButtonClick = False
        elif data["button"] == 4:
            isForwardButtonClick = False
    elif data["type"] == "mousedown":
        if data["button"] == 0:
            isLeftClick = True
        elif data["button"] == 1:
            # await setInitialPos() -> deve ser colocado em uma queue de acoes para ser consumido na thread certa
            pass
        elif data["button"] == 2:
            isRightClick = True
        elif data["button"] == 3:
            isBackButtonClick = True
        elif data["button"] == 4:
            isForwardButtonClick = True
    elif data["type"] == "wheel":
        normalizedDelta = data["delta"] / 100
        shoulderLiftMeta += SCROLL_VEL * -normalizedDelta
        if shoulderLiftMeta > 0:
            shoulderLiftMeta = 0
        elif shoulderLiftMeta < -100:
            shoulderLiftMeta = -100
        elbowFlexMeta += SCROLL_VEL * normalizedDelta
        print(shoulderLiftMeta)
       
        pass
    elif data["type"] == "mousemove":
        shoulderMeta += data["x"] * 50
        if shoulderMeta > 100:
            shoulderMeta = 100
        elif shoulderMeta < -100:
            shoulderMeta = -100
            
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
    global isLeftClick
    global isRightClick
    global isBackButtonClick
    global isForwardButtonClick
    global shoulderMeta
    global elbowFlexMeta
    global shoulderLiftMeta
    
    while True:
        state = follower.get_observation()
        if isRightClick:
            follower.send_action({"gripper.pos": state["gripper.pos"] + 3})
        if isLeftClick:
            follower.send_action({"gripper.pos": state["gripper.pos"] - 3})
        if isBackButtonClick:
            follower.send_action({"wrist_flex.pos": state["wrist_flex.pos"] - 5})
        if isForwardButtonClick:
            follower.send_action({"wrist_flex.pos": state["wrist_flex.pos"] + 5})
        if isQPressed:
            follower.send_action({"wrist_roll.pos": state["wrist_roll.pos"] + 5})
        if isEPressed:
            follower.send_action({"wrist_roll.pos": state["wrist_roll.pos"] - 5})

        follower.send_action({"shoulder_pan.pos": shoulderMeta})
        follower.send_action({
            "elbow_flex.pos": elbowFlexMeta,
            "shoulder_lift.pos": shoulderLiftMeta
        })
        



async def serveWebsocket():
    async with websockets.serve(handler, "172.16.19.183", 6969):
        print("WebSocket server running on ws://127.0.0.1:6969")
        await asyncio.Future()


async def main():
    await setInitialPos()
    camera_loop = threading.Thread(target=cameraStream)
    camera_loop.start()
    main_read_loop = threading.Thread(target=main_robot_loop)
    main_read_loop.start()
    async with websockets.serve(handler, "172.16.19.183", 6969):
        print("WebSocket server running on ws://127.0.0.1:6969")
        await asyncio.Future()
    




if __name__ == "__main__":
    asyncio.run(main())
