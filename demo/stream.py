import os
import time
import queue
import traceback
import threading
import sys

import cv2 as cv

import olympe
import json
import tritonclient.http as httpclient
from tritonclient.utils import *
import visualization_utils as viz_utils
from PIL import Image
import numpy as np

olymp.log.update_config({"loggers": {"olympe": {"level": "WARNING"}}})

DRONE_IP = os.environ.get("DRONE_IP", "192.168.53.1")
DRONE_RTSP_PORT = os.environ.get("DRONE_RTSP_PORT")

# CONSTANT VARIBLES TAKEN FROM rundetector.py
DETECTOR_METADATA = {
    "v5a.0.0": {
        "megadetector_version": "v5a.0.0",
        "typical_detection_threshold": 0.2,
        "conservative_detection_threshold": 0.05,
    },
    "v5b.0.0": {
        "megadetector_version": "v5b.0.0",
        "typical_detection_threshold": 0.2,
        "conservative_detection_threshold": 0.05,
    },
}
DEFAULT_RENDERING_CONFIDENCE_THRESHOLD = DETECTOR_METADATA["v5b.0.0"][
    "typical_detection_threshold"
]
DEFAULT_OUTPUT_CONFIDENCE_THRESHOLD = 0.005
DEFAULT_BOX_THICKNESS = 4
DEFAULT_BOX_EXPANSION = 0
DEFAULT_DETECTOR_LABEL_MAP = {"1": "animal", "2": "person", "3": "vehicle"}


class VideoStream(threading.Thread):
    """
    Custom class to stream video from Parrot Anafi Drone and display using OpenCV window.
    The frames from the camera are sent to MegaDetector to detect if there are any humans or animals present in the frame.
    """

    def __init__(self, FPS: int) -> None:
        self.FPS = FPS
        self.drone = olympe.Drone(DRONE_IP)
        self.frame_queue = queue.Queue()
        self.flush_queue_lock = threading.Lock()
        self.frame_counter = 0
        super().__init__()
        super().start()

    def start(self):
        # Enables a connection to the drone and starts the video stream.

        self.drone.connect()
        self.drone.streaming.set_callbacks(
            raw_cb=self.yuv_frame_cb,
            start_cb=self.start_cb,
            end_cb=self.end_cb,
            flush_raw_cb=self.flush_cb,
        )

        # Start video streaming
        self.drone.streaming.start()

        # Start the connection to Triton Inference Server
        self.client = httpclient.InferenceServerClient(url="localhost:8000")

    def stop(self):
        # Stops all services and disconnects the drone.
        self.drone.streaming.stop()
        self.drone.disconnect()

    def yuv_frame_cb(self, yuv_frame):
        # Callback to reference the frames from the camera and adds them to the queue.
        yuv_frame.ref()
        self.frame_queue.put_nowait(yuv_frame)

    def flush_cb(self, _):
        # Callback to flush the queue and unreferences frames.
        with self.flush_queue_lock:
            while not self.frame_queue.empty():
                self.frame_queue.get_nowait().unref()
        return True

    def start_cb(self):
        pass

    def end_cb(self):
        pass

    def show_yuv_frame(self, window_name, cv_frame):
        # Displays the frame on the screen.
        cv.imshow(window_name, cv_frame)
        cv.waitKey(1)

    def send_to_triton(self, cv_frame):
        # Send the frame to MegaDetector running on Triton Inference Server.

        # Convert the frame to a triton friendly tensor
        input_tensor = [
            httpclient.InferInput("image", cv_frame.shape, datatype="UINT8")
        ]

        input_tensor[0].set_data_from_numpy(cv_frame)

        # Have output tensor ready
        output_tensor = [
            httpclient.InferRequestedOutput("detection_result", binary_data=False)
        ]

        # Send frame to Triton over HTTP
        query_response = self.client.infer(
            model_name="MegaDetector",
            model_version="1",
            inputs=input_tensor,
            outputs=output_tensor,
        )

        # MegaDetector outputs a Python Dictionary with its results.
        # Triton sends it over as a JSON via HTTP.
        # Need to convert the JSON to Python Dictionary and call the 'detections' key.
        triton_output = query_response.as_numpy("detection_result")
        result = json.loads(triton_output[0])

        # Need to convert frame to PIL format.
        image = Image.fromarray(cv_frame)

        # Draws the bounding box to the frame.
        viz_utils.render_detection_bounding_boxes(
            result["detections"],
            image,
            label_map=DEFAULT_DETECTOR_LABEL_MAP,
            confidence_threshold=DEFAULT_RENDERING_CONFIDENCE_THRESHOLD,
            thickness=DEFAULT_BOX_THICKNESS,
            expansion=DEFAULT_BOX_EXPANSION,
        )

        return np.array(image)

    def to_cv_frame(self, yuv_frame):
        # Convert yuv frames to BGR OpenCV
        cvt_color_flag = {
            olympe.VDEF_I420: cv.COLOR_YUV2BGR_I420,
            olympe.VDEF_NV12: cv.COLOR_YUV2BGR_NV12,
        }[yuv_frame.format()]

        cv_frame = cv.cvtColor(yuv_frame.as_ndarray(), cvt_color_flag)
        return cv_frame

    def run(self):
        window_name = "HackOhio"
        cv.namedWindow(window_name, cv.WINDOW_AUTOSIZE)
        main_thread = next(
            filter(lambda t: t.name == "MainThread", threading.enumerate())
        )

        while self.flush_queue_lock:
            # Try to grab frame from the queue.
            try:
                yuv_frame = self.frame_queue.get(timeout=0.01)
                self.frame_counter += 1
            except queue.Empty:
                continue

            # Run detections on frame and display it.
            try:
                cv_frame = self.to_cv_frame(yuv_frame)
                if self.frame_counter % (30 / self.FPS) == 0:
                    cv_frame = self.send_to_triton(cv_frame)
                    self.show_yuv_frame(window_name, cv_frame)
            except Exception:
                traceback.print_exc()
            finally:
                yuv_frame.unref()

        cv.destroyWindow(window_name)


def check_arguments():
    # Check if FPS was provided
    if len(sys.argv) == 1:
        print("No FPS provided")
        return False, None
    # Check if FPS is between 1-30 inclusive
    FPS = int(sys.argv[1])
    if 1 > FPS or FPS > 30:
        print("FPS provided is not between 1 and 30 inclusive")
        return False, None
    # Everything passes
    return True, FPS


if __name__ == "__main__":
    can_run, FPS = check_arguments()
    if can_run:
        cv.startWindowThread()

        stream = VideoStream(FPS)
        stream.start()

        # Run detections on frame and display it.
        while True:
            try:
                time.sleep(1)
            except KeyboardInterrupt:
                break
        stream.stop()
