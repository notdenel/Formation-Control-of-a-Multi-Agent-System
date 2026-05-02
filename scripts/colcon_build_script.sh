cd ~/ros2_ws
./scripts/setup_robot.sh

source ~/.bashrc

echo $ROS_DOMAIN_ID
echo $RMW_IMPLEMENTATION
echo $MACHINE_TYPE

##
cd ~/ros2_ws
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

# Build rf2o once and cache it outside the workspace so it survives rm -rf build install log.
# rf2o_laser_odometry is not compatible with ROS2 Jazzy and must not be rebuilt.
if [ ! -d "$RF2O_CACHE" ]; then
  echo "[INFO] rf2o not yet cached — building rf2o_laser_odometry once (no --symlink-install so install survives clean builds)..."
  colcon build --packages-select rf2o_laser_odometry
  cp -r install/rf2o_laser_odometry "$RF2O_CACHE"
  echo "[INFO] rf2o cached at $RF2O_CACHE"
else
  echo "[INFO] rf2o already cached at $RF2O_CACHE, skipping build."
fi

rm -rf build install log

echo "[INFO] Restoring rf2o from cache..."
mkdir -p install
cp -r "$RF2O_CACHE" install/rf2o_laser_odometry
source install/rf2o_laser_odometry/local_setup.bash 2>/dev/null || true

echo "[INFO] Building full workspace with parallel workers limited to 1..."
colcon build \
  --symlink-install \
  --packages-skip rf2o_laser_odometry \


echo "[INFO] Build complete."
echo "[INFO] Run: source ~/.bashrc"
# echo "[INFO] Run: source ~/ros2_ws/install/setup.bash"

source ~/.bashrc
##

ros2 pkg list | grep ldlidar || true
ros2 pkg list | grep ros_robot_controller || true
ros2 pkg list | grep ros_robot_controller_msgs || true
ros2 pkg list | grep misc || true
ros2 pkg list | grep mentorpi || true
ros2 pkg list | grep rf2o || true

cd ~/ros2_ws
./scripts/enable_swap.sh
./scripts/build_robot.sh
source ~/.bashrc

ls -l /dev/rrc /dev/ldlidar /dev/ttyACM* /dev/ttyUSB* 2>/dev/null

echo "Colcon built"
