#!/usr/bin/env bash
# setup_env.sh — source this on each robot before launching
#
#   source ~/ros2_ws/src/navigation/config/setup_env.sh
#
# It is safe to add this to ~/.bashrc so every new terminal is ready.

# ── ROS2 workspace ────────────────────────────────────────────────────────────
source /opt/ros/jazzy/setup.bash
source ~/ros2_ws/install/setup.bash

# ── DDS: use CycloneDDS (more reliable for multi-robot Pi networks) ───────────
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp

# ── Static peer discovery config ─────────────────────────────────────────────
# Points CycloneDDS at the XML file that lists all robot IPs.
export CYCLONEDDS_URI=file://$HOME/ros2_ws/install/navigation/share/navigation/config/cyclone_dds.xml

# ── ROS domain: keep all three robots on the same isolated domain ─────────────
# This must match on every robot and laptop/RViz terminal.
# Use 10 because it was the last domain known to work in earlier multi-robot tests.
# If the team confirms the latest start_nav tests used 0, change this and
# scripts/setup_robot.sh to 0 together.
export ROS_DOMAIN_ID=10

# ── Robot identity ────────────────────────────────────────────────────────────
# Uncomment the ONE line that matches THIS robot, or set in ~/.bashrc directly.
# export ROBOT_NAME=robot1
# export ROBOT_NAME=robot2
# export ROBOT_NAME=robot3

# ── Hardware profile (required by peripherals and controller packages) ─────────
export MACHINE_TYPE=MentorPi_Mecanum  # mecanum base: enables linear.x, linear.y, angular.z
export LIDAR_TYPE=LD19               # adjust to your lidar model

# Avoid restricting ROS discovery to localhost during multi-robot testing.
unset ROS_AUTOMATIC_DISCOVERY_RANGE
# We are using CycloneDDS XML peers, not the older/nonstandard ROS_STATIC_PEERS env.
unset ROS_STATIC_PEERS

echo "[setup_env] RMW=${RMW_IMPLEMENTATION}  DOMAIN=${ROS_DOMAIN_ID}  ROBOT=${ROBOT_NAME:-unset}"
