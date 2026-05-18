#!/usr/bin/env bash
# setup_env.sh — source this on each robot before launching
#
#   source ~/ros2_ws/src/navigation/config/setup_env.sh
#
# It is safe to add this to ~/.bashrc so every new terminal is ready.

# ── ROS2 workspace ────────────────────────────────────────────────────────────
source /opt/ros/jazzy/setup.bash
source ~/ros2_ws/install/setup.bash

# ── DDS: CycloneDDS (kept for stability; XML peer file is NOT used anymore) ──
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp

# ── Per-machine ROS domain ───────────────────────────────────────────────────
# Robots live in isolated per-robot domains:
#   agent1 / robot1 → 11
#   agent2 / robot2 → 12
#   agent3 / robot3 → 13
# The laptop / fleet observer lives in domain 10. Only the domain_bridge
# process (launched separately via odom_bridge.launch.py on each robot)
# crosses between a robot's private domain and the fleet domain.
case "$(hostname)" in
  agent1) export ROS_DOMAIN_ID=11 ;;
  agent2) export ROS_DOMAIN_ID=12 ;;
  agent3) export ROS_DOMAIN_ID=13 ;;
  *)      export ROS_DOMAIN_ID=10 ;;
esac

# ── Static peers (laptop only) ───────────────────────────────────────────────
# Robots use LOCALHOST discovery; they never need static peers. The laptop
# in domain 10 needs to find each robot's bridge process, so it gets a
# static peer list of every robot IP.
if [ "$ROS_DOMAIN_ID" = "10" ]; then
  export ROS_AUTOMATIC_DISCOVERY_RANGE=SUBNET
  export ROS_STATIC_PEERS=172.31.113.136:172.31.89.63:172.31.115.94
else
  export ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST
  unset ROS_STATIC_PEERS
fi

# ── Robot identity ────────────────────────────────────────────────────────────
# Uncomment the ONE line that matches THIS robot, or set in ~/.bashrc directly.
# export ROBOT_NAME=robot1
# export ROBOT_NAME=robot2
# export ROBOT_NAME=robot3

# ── Hardware profile (required by peripherals and controller packages) ─────────
export MACHINE_TYPE=MentorPi_Mecanum  # mecanum base: enables linear.x, linear.y, angular.z
export LIDAR_TYPE=LD19               # adjust to your lidar model

# Avoid restricting ROS discovery to localhost during multi-robot testing.
# (Discovery range is set above per-domain.)
# CYCLONEDDS_URI is no longer used; domain isolation replaces the XML peer file.
unset CYCLONEDDS_URI

echo "[setup_env] RMW=${RMW_IMPLEMENTATION}  DOMAIN=${ROS_DOMAIN_ID}  ROBOT=${ROBOT_NAME:-unset}"
