#!/usr/bin/env bash
set -euo pipefail

cd "$HOME/ros2_ws"

echo "[INFO] Installing system dependencies..."
sudo apt update
sudo apt install -y \
  build-essential \
  cmake \
  git \
  lsof \
  python3-colcon-common-extensions \
  python3-rosdep \
  python3-vcstool \
  python3-serial \
  python3-yaml \
  python3-numpy \
  python3-transforms3d \
  ros-jazzy-ros-base \
  ros-jazzy-demo-nodes-cpp \
  ros-jazzy-robot-state-publisher \
  ros-jazzy-joint-state-publisher \
  ros-jazzy-xacro \
  ros-jazzy-tf2-ros \
  ros-jazzy-tf2-tools \
  ros-jazzy-robot-localization \
  ros-jazzy-laser-filters \
  ros-jazzy-imu-complementary-filter \
  ros-jazzy-navigation2 \
  ros-jazzy-nav2-bringup \
  ros-jazzy-slam-toolbox \
  ros-jazzy-rmw-cyclonedds-cpp

echo "[INFO] Installing udev rules..."
sudo cp config/udev/99-senior-design-robot.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules
sudo udevadm trigger

echo "[INFO] Adding user to dialout..."
sudo usermod -aG dialout "$USER"

echo "[INFO] Creating servo config placeholder..."
mkdir -p "$HOME/software/Servo_upper_computer"
cat > "$HOME/software/Servo_upper_computer/servo_config.yaml" <<'YAML'
{}
YAML

echo "[INFO] Cleaning old ROS environment lines from .bashrc..."
sed -i '/# >>> senior design ros2 networking >>>/,/# <<< senior design ros2 networking <<</d' "$HOME/.bashrc"
sed -i '/# >>> senior design ros2 >>>/,/# <<< senior design ros2 <<</d' "$HOME/.bashrc"

sed -i \
  -e '/^export ROS_DOMAIN_ID=/d' \
  -e '/^export RMW_IMPLEMENTATION=/d' \
  -e '/^export ROS_AUTOMATIC_DISCOVERY_RANGE=/d' \
  -e '/^export ROS_STATIC_PEERS=/d' \
  -e '/^export ROS_LOCALHOST_ONLY=/d' \
  -e '/^export CYCLONEDDS_URI=/d' \
  -e '/^export MACHINE_TYPE=/d' \
  -e '/^export LIDAR_TYPE=/d' \
  -e '/^export ROBOT_NAME=/d' \
  "$HOME/.bashrc"

echo "[INFO] Writing senior design ROS environment block..."
cat >> "$HOME/.bashrc" <<'BASHRC'

# >>> senior design ros2 >>>
source /opt/ros/jazzy/setup.bash

if [ -f "$HOME/ros2_ws/install/setup.bash" ]; then
  source "$HOME/ros2_ws/install/setup.bash"
fi

case "$(hostname)" in
  agent1) export ROBOT_NAME=robot1 ;;
  agent2) export ROBOT_NAME=robot2 ;;
  agent3) export ROBOT_NAME=robot3 ;;
  *) export ROBOT_NAME="${ROBOT_NAME:-robot}" ;;
esac

export ROS_DOMAIN_ID=10
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export CYCLONEDDS_URI=file://$HOME/ros2_ws/src/navigation/config/cyclone_dds.xml
export MACHINE_TYPE=MentorPi_Mecanum
export LIDAR_TYPE=LD19

unset ROS_AUTOMATIC_DISCOVERY_RANGE
unset ROS_STATIC_PEERS
unset ROS_LOCALHOST_ONLY
# <<< senior design ros2 <<<
BASHRC

echo "[INFO] Setup complete. Reboot recommended because dialout group membership and udev rules may require a new login."
