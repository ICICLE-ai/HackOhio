import os
import sys

# Add all the repos cloned to run MegaDetector to the Python Path
sys.path.append(f"{os.environ['MODEL_REPO']}/MegaDetector/1/")
for path in ["ai4eutils", "camera_traps_MD", "yolov5"]:
    sys.path.append(f"{os.environ['MODEL_REPO']}/MegaDetector/1/{path}")


class MegaDetector:
    def __init__(self):
        # Path model directory (Using Triton Model Repository)
        model_path = f"{ os.environ['MODEL_REPO'] }/MegaDetector/1"

        # Load MegaDetector
        from run_detector_multi import load_detector

        self.model = load_detector(f"{ model_path }/md_v5a.0.0.pt", force_cpu=False)

    def __call__(self, image):
        # Generate detections for one image at a time.
        # TODO: Need to add option for batch version.
        detections = self.model.generate_detections_one_image(image, "", 0.005)

        return detections
