from lerobot.common.cameras.opencv.configuration_opencv import OpenCVCameraConfig
from lerobot.common.cameras.opencv.camera_opencv import OpenCVCamera
from lerobot.common.cameras.configs import ColorMode, Cv2Rotation
import asyncio
from mjpeg_streamer import MjpegServer, Stream
import cv2



async def cameraStream():
    config = OpenCVCameraConfig(
        index_or_path='/dev/video4',
        fps=30,
        width=640,
        height=480,
        color_mode=ColorMode.BGR,
        rotation=Cv2Rotation.NO_ROTATION
    )

    camera = OpenCVCamera(config)
    camera.connect()

    stream = Stream("my_camera", size=(640, 480), quality=50, fps=30)
    server = MjpegServer("0.0.0.0", 8080)
    server.add_stream(stream)
    server.start()

    try:
        while True:
            frame = camera.async_read(timeout_ms=200)
            if frame is not None:
                stream.set_frame(frame)
                cv2.imshow('frame', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            await asyncio.sleep(0.01)
    finally:
        camera.disconnect()
        cv2.destroyAllWindows()
