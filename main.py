import asyncio
import json
import websockets
from lerobot.common.robots.so101_follower import SO101Follower, SO101FollowerConfig
from camera import cameraStream
config = SO101FollowerConfig(
    port="/dev/ttyACM0",
    id="robot",
)
follower = SO101Follower(config)
follower.connect()


#shoulder_pan.pos/shoulder_lift.pos/elbow_flex.pos/wrist_flex.pos/wrist_roll.pos/gripper.pos
#follower.send_action({"shoulder_lift.pos": -100, "gripper.pos": -0})
#print(follower.get_observation())


# from lerobot.common.robots.so101_follower import SO101Follower, SO101FollowerConfig

# config = SO101FollowerConfig(
#     port="/dev/ttyACM0",
#     id="robot",
# )
# follower = SO101Follower(config)
# follower.connect()



def comunicacaoRobo():
    pass
    



isLeftClick = False
isRightClick = False

def jsonInterpreter(data):
    global isLeftClick
    global isRightClick
    state = follower.get_observation()
    if data["type"] == "mouseup":
        if data["button"] == 0:
            isLeftClick = False
        elif data["button"] == 2:
            isRightClick = False
        pass
    elif data["type"] == "mousedown":
        if data["button"] == 0:
            isLeftClick = True
        elif data["button"] == 2:
            isRightClick = True
       
        pass 
    elif data["type"] == "wheel":
        #data["delta"] = data["delta"] / 100
        #print("Wheel " + data["delta"])

        pass
    elif data["type"] == "mousemove":
        follower.send_action({"shoulder_pan.pos": state["shoulder_pan.pos"] + (data["x"] * 50)})
        pass
    else:
        raise ValueError("Unrecognized type")
    
    
async def handler(websocket):
    async for message in websocket:
        data = json.loads(message)
        jsonInterpreter(data)

async def handler(websocket):
    async for message in websocket:
        data = json.loads(message)
        jsonInterpreter(data)

async def non_blocking_loop():
    global isLeftClick
    global isRightClick
    
    while True:
        state = follower.get_observation()
        if isRightClick:
            follower.send_action({"gripper.pos": state["gripper.pos"] + 3})
        if isLeftClick:
            follower.send_action({"gripper.pos": state["gripper.pos"] - 3})
        await asyncio.sleep(0.01)




async def main():
    async with websockets.serve(handler, "172.16.19.183", 6969):
        print("WebSocket server running on ws://127.0.0.1:6969")
        main_robot_loop = asyncio.create_task(non_blocking_loop())
        camera_loop = asyncio.create_task(cameraStream())
        await asyncio.Future()




if __name__ == "__main__":
    asyncio.run(main())
