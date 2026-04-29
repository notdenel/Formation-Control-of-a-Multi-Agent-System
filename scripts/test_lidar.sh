#!/usr/bin/env bash
set -eo pipefail

source /opt/ros/jazzy/setup.bash

if [ -f "$HOME/ros2_ws/install/setup.bash" ]; then
  source "$HOME/ros2_ws/install/setup.bash"
else
  echo "[ERROR] Workspace install/setup.bash not found. Run ./scripts/build_robot.sh first."
  exit 1
fi

echo "[INFO] Checking scan topics..."
ros2 topic list | grep scan || true

echo "[INFO] Checking /scan_raw rate..."
ros2 topic hz /scan_raw --window 20
