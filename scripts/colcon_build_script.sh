#!/usr/bin/env bash
set -eo pipefail

# 1. Setup Environment
cd "$HOME/ros2_ws"
source /opt/ros/jazzy/setup.bash

# 2. Memory Management for small boards
export MAKEFLAGS="-j1"
export CMAKE_BUILD_PARALLEL_LEVEL=1

# 3. Handle the rf2o Cache Logic
RF2O_CACHE="$HOME/.ros2_rf2o_cache"
if [ ! -d "$RF2O_CACHE" ]; then
    echo "[INFO] Building and caching rf2o..."
    colcon build --packages-select rf2o_laser_odometry
    mkdir -p "$RF2O_CACHE"
    cp -r install/rf2o_laser_odometry "$RF2O_CACHE"
fi

# 4. Clean and Restore
rm -rf build install log
mkdir -p install
cp -r "$RF2O_CACHE" install/rf2o_laser_odometry

# 5. The Main Build (Skip the cached rf2o to avoid conflicts)
echo "[INFO] Building workspace..."
colcon build \
  --symlink-install \
  --packages-skip rf2o_laser_odometry \#!/usr/bin/env bash
set -eo pipefail

# 1. Setup Environment
cd "$HOME/ros2_ws"
source /opt/ros/jazzy/setup.bash

# 2. Memory Management for small boards
export MAKEFLAGS="-j1"
export CMAKE_BUILD_PARALLEL_LEVEL=1

# 3. Handle the rf2o Cache Logic
RF2O_CACHE="$HOME/.ros2_rf2o_cache"
if [ ! -d "$RF2O_CACHE" ]; then
    echo "[INFO] Building and caching rf2o..."
    colcon build --packages-select rf2o_laser_odometry
    mkdir -p "$RF2O_CACHE"
    cp -r install/rf2o_laser_odometry "$RF2O_CACHE"
fi

# 4. Clean and Restore
rm -rf build install log
mkdir -p install
cp -r "$RF2O_CACHE" install/rf2o_laser_odometry

# 5. The Main Build (Skip the cached rf2o to avoid conflicts)
echo "[INFO] Building workspace..."
colcon build \
  --symlink-install \
  --packages-skip rf2o_laser_odometry \
  --parallel-workers 1

# 6. Final Setup
source install/setup.bash
echo "Build complete. Remember to: source ~/ros2_ws/install/setup.bash"

# 6. Final Setup
source install/setup.bash
echo "Build complete. Remember to: source ~/ros2_ws/install/setup.bash"