#!/usr/bin/env bash
set -eo pipefail

cd "$HOME/ros2_ws"

if [ ! -f /opt/ros/jazzy/setup.bash ]; then
  echo "[ERROR] /opt/ros/jazzy/setup.bash not found. Is ROS2 Jazzy installed?"
  exit 1
fi

source /opt/ros/jazzy/setup.bash

export MAKEFLAGS="-j1"
export CMAKE_BUILD_PARALLEL_LEVEL=1

rm -rf build install log

echo "[INFO] Building full workspace with parallel workers limited to 1..."
colcon build --symlink-install --parallel-workers 1

echo "[INFO] Build complete."
echo "[INFO] Run: source ~/.bashrc"
# echo "[INFO] Run: source ~/ros2_ws/install/setup.bash"
