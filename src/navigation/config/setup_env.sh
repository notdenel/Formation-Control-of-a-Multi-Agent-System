#!/usr/bin/env bash
# setup_env.sh — source this on each robot and on the WSL coordinator.
#
#   source ~/ros2_ws/src/navigation/config/setup_env.sh
#
# Domain layout:
#   agent1 / robot1  ROS_DOMAIN_ID 11
#   agent2 / robot2  ROS_DOMAIN_ID 12
#   agent3 / robot3  ROS_DOMAIN_ID 13
#   WSL coordinator  ROS_DOMAIN_ID 10   (RViz, diagnostics, pose_aggregator)
#
# Each robot's real_robot.launch.py starts a domain_bridge (odom_bridge.launch.py)
# that joins both the robot's private domain and domain 10.  The bridge shares
# /robotX/odom and /robotX/amcl_pose outbound and receives peer /robotY/odom
# inbound.  Aggregation runs on each robot in its private domain; no cmd_vel
# ever crosses a domain boundary.
#
# Robots use LOCALHOST discovery so private-domain traffic stays on-device.
# domain_bridge gets CYCLONEDDS_URI from real_robot.launch.py so its domain-10
# participant can reach the WSL coordinator across WiFi.
# WSL uses SUBNET to observe the fleet domain from outside.

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
# Robots: LOCALHOST keeps private-domain traffic on-device (no accidental
#   cross-machine multicast for the robot's internal topics).
# WSL: SUBNET so it can observe domain 10 participants across WiFi.
if [ "${ROS_DOMAIN_ID}" = "10" ]; then
  export ROS_AUTOMATIC_DISCOVERY_RANGE=SUBNET
else
  export ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST
fi

# ── CycloneDDS static peer XML ────────────────────────────────────────────────
# real_robot.launch.py sets CYCLONEDDS_URI for launched processes; this export
# covers any tools run directly in the shell (ros2 topic list, rviz2, etc.).
export CYCLONEDDS_URI="file://$HOME/ros2_ws/src/navigation/config/cyclone_dds.xml"

# ── Static peer IPs ───────────────────────────────────────────────────────────
# Run `hostname -I` on each machine to confirm; update if DHCP changes them.
ROBOT1_IP=172.31.113.136
ROBOT2_IP=172.31.89.63
ROBOT3_IP=172.31.115.94
WSL_IP=172.31.78.102

case "$(hostname)" in
  agent1) export ROS_STATIC_PEERS="${ROBOT2_IP}:${ROBOT3_IP}:${WSL_IP}" ;;
  agent2) export ROS_STATIC_PEERS="${ROBOT1_IP}:${ROBOT3_IP}:${WSL_IP}" ;;
  agent3) export ROS_STATIC_PEERS="${ROBOT1_IP}:${ROBOT2_IP}:${WSL_IP}" ;;
  *)      export ROS_STATIC_PEERS="${ROBOT1_IP}:${ROBOT2_IP}:${ROBOT3_IP}" ;;
esac

# ── Hardware profile ──────────────────────────────────────────────────────────
export MACHINE_TYPE=MentorPi_Mecanum
export LIDAR_TYPE=LD19

echo "[setup_env] RMW=${RMW_IMPLEMENTATION}  DOMAIN=${ROS_DOMAIN_ID}  ROBOT=${ROBOT_NAME}"
echo "[setup_env] STATIC_PEERS=${ROS_STATIC_PEERS}"
