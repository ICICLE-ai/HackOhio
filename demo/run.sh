#!/bin/bash
#
# Author: Carlos Guzman (guzman.109@osu.edu)
# 
# This script is used to run the HackOhio demo.
#
# Two input varaibles required.
#   PYTHON_PATH: The path to venv python with install requirements
#   DEMO_VERSION: The version of demo, ie run MegaDetector locally or with Triton Inference Server
#
# Examples:
#   sh run.sh 30 .venv/bin/python3.9
#   sh run.sh .venv/bin/python3.9
#
# Required for KDE Plasma to output OpenCV frame. Should be safe to use for Gnome
export QT_QPA_PLATFORM=xcb;

# Required for Wayland sessions only. Should be safe to use for X11.
export PYOPENGL_PLATFORM=glx;

export FPS=$1

# Execute the demo
$2 HackOhio/demo/stream-local.py
