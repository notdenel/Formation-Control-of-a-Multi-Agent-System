#!/usr/bin/env bash
set -euo pipefail

cd "$HOME/ros2_ws"

if [ ! -f /opt/ros/jazzy/setup.bash ]; then
  echo "[ERROR] /opt/ros/jazzy/setup.bash not found. Is ROS2 Jazzy installed?"
  exit 1
fi

set +u
source /opt/ros/jazzy/setup.bash
set -u

export MAKEFLAGS="-j1"
export CMAKE_BUILD_PARALLEL_LEVEL=1

echo "[INFO] Cleaning workspace build/install/log..."
rm -rf build install log

echo "[INFO] Building base workspace packages, skipping rf2o_laser_odometry and navigation first..."
colcon build \
  --symlink-install \
  --packages-skip rf2o_laser_odometry navigation

source "$HOME/ros2_ws/install/setup.bash"

echo "[INFO] Building rf2o_laser_odometry..."
colcon build \
  --symlink-install \
  --parallel-workers 1 \
  --packages-select rf2o_laser_odometry \
  --event-handlers console_direct+ \
  --cmake-args -DCMAKE_BUILD_TYPE=Release

source "$HOME/ros2_ws/install/setup.bash"

echo "[INFO] Building navigation..."
colcon build \
  --symlink-install \
  --parallel-workers 1 \
  --packages-select navigation

source "$HOME/ros2_ws/install/setup.bash"

echo "[INFO] Build complete."
echo "[INFO] Run: source ~/.bashrc"
