#!/usr/bin/env bash
set -euo pipefail

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

echo "[INFO] Updating bashrc ROS environment block..."
sed -i '/# >>> senior design ros2 >>>/,/# <<< senior design ros2 <<</d' "$HOME/.bashrc"

cat >> "$HOME/.bashrc" <<'BASHRC'

# >>> senior design ros2 >>>
source /opt/ros/jazzy/setup.bash
source ~/ros2_ws/install/setup.bash
export ROS_DOMAIN_ID=10
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
export MACHINE_TYPE=MentorPi_Mecanum
# <<< senior design ros2 <<<
BASHRC

echo "[INFO] Setup complete. Reboot recommended."
