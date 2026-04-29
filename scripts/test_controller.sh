#!/usr/bin/env bash
set -eo pipefail

source /opt/ros/jazzy/setup.bash

if [ -f "$HOME/ros2_ws/install/setup.bash" ]; then
  source "$HOME/ros2_ws/install/setup.bash"
else
  echo "[ERROR] Workspace install/setup.bash not found. Run ./scripts/build_robot.sh first."
  exit 1
fi

echo "[INFO] Checking controller topics..."
ros2 topic list | grep -E "cmd_vel|odom|imu|battery|controller|ros_robot" || true

echo "[INFO] Checking IMU rate..."
ros2 topic hz /ros_robot_controller/imu_raw --window 20
