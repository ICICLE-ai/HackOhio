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
#   1) Run MegaDetector locally  
#       sh run.sh HackOhio/.venv/bin/python3.9 local 
#   2) Run MegaDetector with Triton
#       sh run.sh HackOhio/.venv/bin/python3.9 triton

PYTHON_PATH=$2

# Required for KDE Plasma to output OpenCV frame. Should be safe to use for Gnome
export QT_QPA_PLATFORM=xcb;

# Required for Wayland sessions only. Should be safe to use for X11.
export PYOPENGL_PLATFORM=glx;

# Required path for non-local version.
export MODEL_REPO=$3

# Execute the demo
$2 HackOhio/demo/stream-local.py $1
