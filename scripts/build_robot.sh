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

RF2O_CACHE="$HOME/.ros2_rf2o_cache"

rm -rf build install log

if [ -d "$RF2O_CACHE" ]; then
  echo "[INFO] Restoring rf2o from cache..."
  mkdir -p install
  cp -r "$RF2O_CACHE" install/rf2o_laser_odometry
  source install/rf2o_laser_odometry/local_setup.bash 2>/dev/null || true
fi

echo "[INFO] Building full workspace with parallel workers limited to 1..."
colcon build --symlink-install --parallel-workers 1 --packages-skip rf2o_laser_odometry

echo "[INFO] Build complete."
echo "[INFO] Run: source ~/.bashrc"
# echo "[INFO] Run: source ~/ros2_ws/install/setup.bash"
