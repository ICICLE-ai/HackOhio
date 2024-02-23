# Demo for HackOhio Hackathon at Columbus School for Girls
## Summary
This demo uses ICICLE's [**Camera-Traps**](https://github.com/tapis-project/camera-traps) version of [**MegaDetector**](https://github.com/microsoft/CameraTraps/tree/main) on a video stream coming from a **Parrot Anafi** drone. This version of MegaDetector can detect and classify whether there is **person, animal, or vehicle** in the frame. For safety reasons, the drone follows movement commands from its controller only, connected to your computer. 

This version runs MegaDetector on your local machine as a local Python Class. MegaDetector is pretty heavy to run so make sure your machine can use it.   
## Dependencies
A list of dependencies for both version are as follows,
1) Linux Operating System
	* The [*parrot-olympe*](https://pypi.org/project/parrot-olympe/) PyPI package only works on Linux. Ubuntu 23.10 was specifically used but other distributions should work as well.
2) Python 3.9.18 & pip

[*pyenv*](https://github.com/pyenv/pyenv) is a great tool to use any version of Python. Due to *Pillow v9.40* needed as a requirement. Do not upgrade Pillow because newer versions past *9.4.0* deprecated some of the functions used.

If using pyenv, then run
>`pyenv install 3.9`
>`pyenv virtualenv 3.9 demo-venv`
>`pyenv activate demo-venv`
>`pip install --upgrade pip setuptools wheel`

To install the python libraries simply run,
>`pip install -r requirements.txt`

Lastly, download the required files to run MegaDetector from this [link](https://drive.google.com/file/d/1LEAJ8FVeAPC6woKEivi8ZyMWw933wecb/view?usp=sharing) and extract using gnu tar with the following command (make sure you download to the project folder */HackOhio*),
>`tar -xzf MegaDetector.tar.gz`

## Run the Demo
In order to run the demo you need to connect the Anafi Controller to your computer with the provided USB-A to USB-C cable. Connect the USB-C side to the Anafi Controller and the USB-A side to your computer.

Once the controller has been connected to your computer, go to your network settings and change your network to the wired connection with name that starts with **eth** .

For convenience a script *run.sh* is provided for you. It requires the following parameters,
* Desired Frames per Second (1-30 inclusive)
* Path to python environment

For example,
>`sh run.sh 30 demo-venv/bin/python` 

## Troubleshoot
If you are experiencing significant lag then try playing around with the FPS. 

MegaDetector is a heavy model to use so you may require a GPU. The provided MegaDetector files should detect and use the GPU. If not then you can look at `demo/MegaDetectorLocal.py` or `MegaDetector/run_detector_multi.py` to see if the flag has been set.
