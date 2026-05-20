#!/usr/bin/env bash
# setup_env.sh — source this on each robot and on the coordinator laptop.
#
#   source ~/ros2_ws/src/navigation/config/setup_env.sh
#
# Domain layout:
#   agent1 / robot1  → ROS_DOMAIN_ID 11
#   agent2 / robot2  → ROS_DOMAIN_ID 12
#   agent3 / robot3  → ROS_DOMAIN_ID 13
#   laptop / WSL     → ROS_DOMAIN_ID 10  (fleet observer, RViz, diagnostics)
#
# Each robot runs domain_bridge (started by real_robot.launch.py) which joins
# both its private domain and domain 10.  The bridge shares /robotX/odom and
# receives peer /robotY/odom and /robotZ/odom for local aggregation.
# No cmd_vel crosses the domain boundary — aggregation runs on each robot.
#
# Robots use LOCALHOST discovery so private-domain traffic stays on-device.
# domain_bridge inherits CYCLONEDDS_URI (set by real_robot.launch.py) and
# uses the static-peer XML to reach domain 10 participants across WiFi.
# The laptop uses SUBNET so it can observe the fleet domain from WSL.

source /opt/ros/jazzy/setup.bash
source ~/ros2_ws/install/setup.bash

# ── RMW ───────────────────────────────────────────────────────────────────────
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp

# ── Per-machine domain + robot name ──────────────────────────────────────────
case "$(hostname)" in
  agent1) export ROS_DOMAIN_ID=11 ; export ROBOT_NAME=robot1 ;;
  agent2) export ROS_DOMAIN_ID=12 ; export ROBOT_NAME=robot2 ;;
  agent3) export ROS_DOMAIN_ID=13 ; export ROBOT_NAME=robot3 ;;
  *)      export ROS_DOMAIN_ID=10 ; export ROBOT_NAME=coordinator ;;
esac

# ── Discovery range ───────────────────────────────────────────────────────────
# Robots: LOCALHOST — private domain nodes never need cross-machine multicast.
# Laptop: SUBNET — must reach each robot's domain_bridge on domain 10.
if [ "${ROS_DOMAIN_ID}" = "10" ]; then
  export ROS_AUTOMATIC_DISCOVERY_RANGE=SUBNET
else
  export ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST
fi

# ── CycloneDDS static peer XML ────────────────────────────────────────────────
# real_robot.launch.py sets CYCLONEDDS_URI for launched processes; this export
# covers any tools run directly in the shell (e.g. ros2 topic list, rviz2).
export CYCLONEDDS_URI="file://$HOME/ros2_ws/src/navigation/config/cyclone_dds.xml"

# ── Static peer list ──────────────────────────────────────────────────────────
# Run `hostname -I` on each machine to confirm IPs; update if DHCP changes them.
ROBOT1_IP=172.31.113.136
ROBOT2_IP=172.31.89.63
ROBOT3_IP=172.31.115.94
LAPTOP_IP=172.31.78.102

case "$(hostname)" in
  agent1) export ROS_STATIC_PEERS="${ROBOT2_IP}:${ROBOT3_IP}:${LAPTOP_IP}" ;;
  agent2) export ROS_STATIC_PEERS="${ROBOT1_IP}:${ROBOT3_IP}:${LAPTOP_IP}" ;;
  agent3) export ROS_STATIC_PEERS="${ROBOT1_IP}:${ROBOT2_IP}:${LAPTOP_IP}" ;;
  *)      export ROS_STATIC_PEERS="${ROBOT1_IP}:${ROBOT2_IP}:${ROBOT3_IP}" ;;
esac

# ── Hardware profile ──────────────────────────────────────────────────────────
export MACHINE_TYPE=MentorPi_Mecanum
export LIDAR_TYPE=LD19

echo "[setup_env] RMW=${RMW_IMPLEMENTATION}  DOMAIN=${ROS_DOMAIN_ID}  ROBOT=${ROBOT_NAME}"
echo "[setup_env] STATIC_PEERS=${ROS_STATIC_PEERS}"
