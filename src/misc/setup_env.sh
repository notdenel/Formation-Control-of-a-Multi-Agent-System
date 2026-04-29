#!/bin/bash
# ─────────────────────────────────────────────────────────────
# ROS2 workspace environment — source this before running anything
#   source ~/ros2_ws/setup_env.sh
# ─────────────────────────────────────────────────────────────

# ── Robot type ───────────────────────────────────────────────
# Options seen in source: MentorPi_Mecanum, MentorPi_Acker
# MentorPi (standard diff-drive) may also be valid — check your hardware
export MACHINE_TYPE=MentorPi_Mecanum

# ── Network ──────────────────────────────────────────────────
# HOST is used by teleop_key_control to know which machine to connect to.
# For local single-machine testing, use localhost.
# On the real robot, set this to the robot's IP address.
export HOST=localhost

# ── LiDAR ────────────────────────────────────────────────────
# Used by lidar.launch.py and lidar_view.launch.py
# Common values: LD06, LD19, STL27L — check the label on your LiDAR unit
export LIDAR_TYPE=LD06

# ── Depth camera ─────────────────────────────────────────────
# Used by depth_camera.launch.py
# Common values: D435, D435i, Astra
export DEPTH_CAMERA_TYPE=D435

# ── Build flag ───────────────────────────────────────────────
# Most launch files check need_compile to decide whether to rebuild.
# Set to False for normal operation (workspace already built).
export need_compile=False

# ── ROS2 overlay ─────────────────────────────────────────────
source /opt/ros/jazzy/setup.bash
source ~/ros2_ws/install/setup.bash

echo "✓ Environment ready"
echo "  MACHINE_TYPE     = $MACHINE_TYPE"
echo "  HOST             = $HOST"
echo "  LIDAR_TYPE       = $LIDAR_TYPE"
echo "  DEPTH_CAMERA_TYPE= $DEPTH_CAMERA_TYPE"
echo "  need_compile     = $need_compile"
