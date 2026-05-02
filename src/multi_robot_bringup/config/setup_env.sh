#!/usr/bin/env bash
# setup_env.sh — source this on each robot before launching
#
#   source ~/ros2_ws/src/multi_robot_bringup/config/setup_env.sh
#
# It is safe to add this to ~/.bashrc so every new terminal is ready.

# ── ROS2 workspace ────────────────────────────────────────────────────────────
source /opt/ros/jazzy/setup.bash
source ~/ros2_ws/install/setup.bash

# ── DDS: use CycloneDDS (more reliable for multi-robot Pi networks) ───────────
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp

# ── Static peer discovery config ─────────────────────────────────────────────
# Points CycloneDDS at the XML file that lists all robot IPs.
export CYCLONEDDS_URI=~/ros2_ws/src/multi_robot_bringup/config/cyclone_dds.xml

# ── ROS domain: keep all three robots on the same isolated domain ─────────────
# Change this if you share a LAN with other ROS2 systems.
export ROS_DOMAIN_ID=0

# ── Robot identity ────────────────────────────────────────────────────────────
# Uncomment the ONE line that matches THIS robot, or set in ~/.bashrc directly.
# export ROBOT_NAME=robot1
# export ROBOT_NAME=robot2
# export ROBOT_NAME=robot3

# ── Hardware profile (required by peripherals and controller packages) ─────────
export MACHINE_TYPE=MentorPi_Acker   # adjust to your platform
export LIDAR_TYPE=LD19               # adjust to your lidar model

echo "[setup_env] RMW=${RMW_IMPLEMENTATION}  DOMAIN=${ROS_DOMAIN_ID}  ROBOT=${ROBOT_NAME:-unset}"
