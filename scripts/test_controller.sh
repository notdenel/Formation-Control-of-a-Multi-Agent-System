#!/usr/bin/env bash
set -euo pipefail

ROBOT_NAME="${1:-${ROBOT_NAME:-robot2}}"

cd "$HOME/ros2_ws"
source /opt/ros/jazzy/setup.bash

if [ -f "$HOME/ros2_ws/install/setup.bash" ]; then
  source "$HOME/ros2_ws/install/setup.bash"
fi

if [ -f "$HOME/ros2_ws/src/navigation/config/setup_env.sh" ]; then
  source "$HOME/ros2_ws/src/navigation/config/setup_env.sh"
fi

unset ROS_AUTOMATIC_DISCOVERY_RANGE
unset ROS_STATIC_PEERS
unset ROS_LOCALHOST_ONLY
export ROS2CLI_NO_DAEMON=1

echo "[INFO] Checking controller command topic for ${ROBOT_NAME}..."
ros2 topic info "/${ROBOT_NAME}/controller/cmd_vel" -v

echo "[INFO] Checking raw controller IMU..."
ros2 topic hz "/${ROBOT_NAME}/ros_robot_controller/imu_raw" --window 20

echo "[INFO] Checking filtered IMU..."
ros2 topic hz "/${ROBOT_NAME}/imu" --window 20
