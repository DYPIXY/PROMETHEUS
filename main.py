import asyncio
import json
import websockets
import threading
import numpy as np
import cv2
import base64

import hand_tracking

from lerobot.common.robots.so101_follower import SO101Follower, SO101FollowerConfig
from camera import cameraStream
config = SO101FollowerConfig(
    port="/dev/ttyACM0",
    id="robot",
)
follower = SO101Follower(config)
follower.connect()


#shoulder_pan.pos/shoulder_lift.pos/elbow_flex.pos/wrist_flex.pos/wrist_roll.pos/gripper.pos
initialPos = {'shoulder_pan.pos': 3, 'shoulder_lift.pos': 0, 'elbow_flex.pos': -90, 'wrist_flex.pos': -83, 'wrist_roll.pos': 1, 'gripper.pos': 14}


SCROLL_VEL = 6
VELOCITY = 7
isBackButtonClick = False
isForwardButtonClick = False
isQPressed = False
isEPressed = False
isOpeningClamp = False
isClosingClamp = False

async def setInitialPos():
    global state
    global shoulderMeta
    global shoulderLiftMeta
    global elbowFlexMeta
    global gripperMeta
    global wristRollMeta
    global wristFlexMeta
    follower.send_action(initialPos)
    await asyncio.sleep(2)
    # follower.send_t_action({"delta_x": 0.1})
    # await asyncio.sleep(2)

    state = follower.get_observation()
    shoulderMeta = state["shoulder_pan.pos"] 
    shoulderLiftMeta = state["shoulder_lift.pos"]
    elbowFlexMeta = state["elbow_flex.pos"]
    gripperMeta = state["gripper.pos"]
    wristRollMeta = state["wrist_roll.pos"]
    wristFlexMeta = state["wrist_flex.pos"]


def moveZ(value):
    global elbowFlexMeta
    global shoulderLiftMeta
    shoulderLiftMeta += SCROLL_VEL * 2 * -value
    if shoulderLiftMeta > 0:
        shoulderLiftMeta = 0
    elif shoulderLiftMeta < -100:
        shoulderLiftMeta = -100
    elbowFlexMeta += SCROLL_VEL * value
    if elbowFlexMeta > 0:
        elbowFlexMeta = 0
    elif elbowFlexMeta < -90:
        elbowFlexMeta = -90

def moveY(value):
    global elbowFlexMeta
    global shoulderLiftMeta
    shoulderLiftMeta += SCROLL_VEL * -value
    if shoulderLiftMeta > 0:
        shoulderLiftMeta = 0
    elif shoulderLiftMeta < -100:
        shoulderLiftMeta = -100
    elbowFlexMeta += SCROLL_VEL * value
    if elbowFlexMeta > 0:
        elbowFlexMeta = 0
    elif elbowFlexMeta < -90:
        elbowFlexMeta = -90


async def jsonInterpreter(data):
    global isOpeningClamp
    global isClosingClamp
    global isBackButtonClick
    global isForwardButtonClick
    global isEPressed
    global isQPressed
    global shoulderMeta
    global elbowFlexMeta
    global shoulderLiftMeta
    global gripperMeta
    global wristFlexMeta
    global wristRollMeta


    if data["type"] == "mouseup":
        if data["button"] == 0:
            isClosingClamp = False
        elif data["button"] == 2:
            isOpeningClamp = False
        elif data["button"] == 3:
            isBackButtonClick = False
        elif data["button"] == 4:
            isForwardButtonClick = False
    elif data["type"] == "mousedown":
        if data["button"] == 0:
            isClosingClamp = True
        elif data["button"] == 1:
            # await setInitialPos() -> deve ser colocado em uma queue de acoes para ser consumido na thread certa
            pass
        elif data["button"] == 2:
            isOpeningClamp = True
        elif data["button"] == 3:
            isBackButtonClick = True
        elif data["button"] == 4:
            isForwardButtonClick = True
    elif data["type"] == "wheel":
        normalizedDelta = data["delta"] / 100
        moveY(normalizedDelta)

    elif data["type"] == "mousemove":
        shoulderMeta += data["x"] * 50
        if shoulderMeta > 100:
            shoulderMeta = 100
        elif shoulderMeta < -100:
            shoulderMeta = -100



        normalizedDelta = data["y"] * -4
        moveZ(normalizedDelta)
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
    elif data["type"] == "webcam_frame":
        img_b64 = data["data"]

        # --- IMPORTANT: Strip data URI prefix if present ---
        if "," in img_b64 and img_b64.startswith("data:"):
            img_b64 = img_b64.split(",")[1]

        try:
            decoded_data = base64.b64decode(img_b64)
        except Exception:
            return # Stop processing if decoding fails
        
        np_data = np.frombuffer(decoded_data, np.uint8)
        img = cv2.imdecode(np_data,cv2.IMREAD_UNCHANGED)

        if img is None:
            return # Stop here if img is None

        (avg_closure, positionDeltas, anglesDeltas) = hand_tracking.get_hand_data(img)
        (deltaX, deltaY, deltaZ) = positionDeltas
        (angXDelta, angYDelta, angZDelta) = anglesDeltas
        moveZ(deltaZ * 15000000)
        moveY(deltaY * 250)
        shoulderMeta += -deltaX * 900
        wristRollMeta += angXDelta * 20
        wristFlexMeta += angZDelta * -5000
        if avg_closure is not None:
            gripperMeta = avg_closure
        # print(avg_closure)
        # isClosingClamp = not isOpeningClamp
        # clampPercentage = hand_tracking.get_hand_closure_percentage(img)
        # print(clampPercentage)
        
        
        
    else:
        raise ValueError("Unrecognized type")
    
    


async def handler(websocket):
    async for message in websocket:
        data = json.loads(message)
        await jsonInterpreter(data)

def main_robot_loop():
    global follower
    global isBackButtonClick
    global isForwardButtonClick
    global shoulderMeta
    global elbowFlexMeta
    global shoulderLiftMeta
    global gripperMeta
    global isOpeningClamp
    global isClosingClamp
    global wristFlexMeta
    global wristRollMeta
    
    
    while True:
        state = follower.get_observation()
        if isBackButtonClick:
            follower.send_action({"wrist_flex.pos": state["wrist_flex.pos"] - 10})
        if isForwardButtonClick:
            follower.send_action({"wrist_flex.pos": state["wrist_flex.pos"] + 10})
        if isQPressed:
            follower.send_action({"wrist_roll.pos": state["wrist_roll.pos"] + 5})
        if isEPressed:
            follower.send_action({"wrist_roll.pos": state["wrist_roll.pos"] - 5})



        if isOpeningClamp:
            gripperMeta += 0.1
        if isClosingClamp:
            gripperMeta -= 0.1

        if gripperMeta < 0:
            gripperMeta = 0
        if gripperMeta > 100:
            gripperMeta = 100

        follower.send_action({
            "elbow_flex.pos": elbowFlexMeta,
            "shoulder_lift.pos": shoulderLiftMeta,
            "shoulder_pan.pos": shoulderMeta,
            "gripper.pos": gripperMeta,
            #"wrist_roll.pos": wristRollMeta,
            #"wrist_flex.pos": wristFlexMeta
        })
        





async def main():
    await setInitialPos()
    camera_loop = threading.Thread(target=cameraStream)
    camera_loop.start()
    main_read_loop = threading.Thread(target=main_robot_loop)
    main_read_loop.start()
    async with websockets.serve(handler, "0.0.0.0", 6969):
        print("WebSocket server running on ws://127.0.0.1:6969")
        await asyncio.Future()
    




if __name__ == "__main__":
    asyncio.run(main())
