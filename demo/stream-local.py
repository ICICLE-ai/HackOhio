import os
import time
import queue
import traceback
import threading

import cv2 as cv
import olympe
# import json
import visualization_utils as viz_utils
from PIL import Image
import numpy as np

from MegaDetectorLocal import MegaDetector

olympe.log.update_config({"loggers": {"olympe": {"level": "WARNING"}}})

DRONE_IP = os.environ.get("DRONE_IP", "192.168.53.1")
DRONE_RTSP_PORT = os.environ.get("DRONE_RTSP_PORT")
FPS = int(os.environ.get("FPS", "30"))

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

    def __init__(self) -> None:
        self.drone = olympe.Drone(DRONE_IP)
        self.frame_queue = queue.Queue()
        self.flush_queue_lock = threading.Lock()
        self.frame_counter = 0
        self.model = MegaDetector()
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

    def detect(self, cv_frame):
        # Send frames to MegaDetector to run detections.
        result = self.model(cv_frame)

        # Need to convert frame to PIL format.
        image = Image.fromarray(cv_frame)

        # Draws the bounding box to the frame
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
                if self.frame_counter % (30 // FPS) == 0: # Desired FPS (Using integer division only)
                    cv_frame = self.detect(cv_frame)
                    self.show_yuv_frame(window_name, cv_frame)
            except Exception:
                traceback.print_exc()
            finally:
                yuv_frame.unref()

        cv.destroyWindow(window_name)


if __name__ == "__main__":
    cv.startWindowThread()

    stream = VideoStream()
    stream.start()

    # Continues running until killed via keyboard.
    while True:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            break
    stream.stop()
