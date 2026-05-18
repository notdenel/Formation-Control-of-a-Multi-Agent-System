#!/usr/bin/env bash
# setup_env.sh — source this on each robot and on the coordinator laptop.
#
#   source ~/ros2_ws/src/navigation/config/setup_env.sh
#
# Strategy: each robot lives in its OWN ROS_DOMAIN_ID. The coordinator
# laptop lives in domain 10. A domain_bridge process running on the laptop
# (started by infrastructure.launch.py) joins both domains and bridges
# /robotN/odom and /robotN/controller/cmd_vel. CycloneDDS handles the
# wire transport via SUBNET discovery + a static peer list.

# ── ROS2 workspace ────────────────────────────────────────────────────────────
source /opt/ros/jazzy/setup.bash
source ~/ros2_ws/install/setup.bash

<<<<<<< HEAD
# ── DDS ───────────────────────────────────────────────────────────────────────
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp

# ── Per-machine ROS domain ───────────────────────────────────────────────────
case "$(hostname)" in
  agent1) export ROS_DOMAIN_ID=11 ; export ROBOT_NAME=robot1 ;;
  agent2) export ROS_DOMAIN_ID=12 ; export ROBOT_NAME=robot2 ;;
  agent3) export ROS_DOMAIN_ID=13 ; export ROBOT_NAME=robot3 ;;
  *)      export ROS_DOMAIN_ID=10 ;;   # laptop / coordinator
esac

# ── Discovery: SUBNET on every machine, with explicit static peers ───────────
# Robots used to be LOCALHOST-only, which prevented the laptop's
# domain_bridge from ever seeing /robotN/odom across the WiFi. Every
# machine now advertises over wlan0 and statically points at the others.
export ROS_AUTOMATIC_DISCOVERY_RANGE=SUBNET
=======
# ── DDS: CycloneDDS (kept for stability; XML peer file is NOT used anymore) ──
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp

# ── Per-machine ROS domain ───────────────────────────────────────────────────
# Robots live in isolated per-robot domains:
#   agent1 / robot1 → 11
#   agent2 / robot2 → 12
#   agent3 / robot3 → 13
# The laptop / fleet observer lives in domain 10. Only the domain_bridge
# process (launched separately via odom_bridge.launch.py on each robot)
# crosses between a robot's private domain and the fleet domain.
case "$(hostname)" in
  agent1) export ROS_DOMAIN_ID=11 ;;
  agent2) export ROS_DOMAIN_ID=12 ;;
  agent3) export ROS_DOMAIN_ID=13 ;;
  *)      export ROS_DOMAIN_ID=10 ;;
esac

# ── Static peers (laptop only) ───────────────────────────────────────────────
# Robots use LOCALHOST discovery; they never need static peers. The laptop
# in domain 10 needs to find each robot's bridge process, so it gets a
# static peer list of every robot IP.
if [ "$ROS_DOMAIN_ID" = "10" ]; then
  export ROS_AUTOMATIC_DISCOVERY_RANGE=SUBNET
  export ROS_STATIC_PEERS=172.31.113.136:172.31.89.63:172.31.115.94
else
  export ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST
  unset ROS_STATIC_PEERS
fi
>>>>>>> 4410796 (Added topic bridges so only relevant topics are shared between robots improving battery life, tried to add slam positioning, implementing formation control)

# Edit ROBOT_IPS / LAPTOP_IP whenever the WiFi hands out new addresses.
ROBOT1_IP=172.31.113.136
ROBOT2_IP=172.31.89.63
ROBOT3_IP=172.31.115.94
LAPTOP_IP=172.31.78.102   # ← `hostname -I` on the WSL laptop; update if it changes

# Static peer list = every participant EXCEPT this machine.
case "$(hostname)" in
  agent1) export ROS_STATIC_PEERS="${ROBOT2_IP}:${ROBOT3_IP}:${LAPTOP_IP}" ;;
  agent2) export ROS_STATIC_PEERS="${ROBOT1_IP}:${ROBOT3_IP}:${LAPTOP_IP}" ;;
  agent3) export ROS_STATIC_PEERS="${ROBOT1_IP}:${ROBOT2_IP}:${LAPTOP_IP}" ;;
  *)      export ROS_STATIC_PEERS="${ROBOT1_IP}:${ROBOT2_IP}:${ROBOT3_IP}" ;;
esac

<<<<<<< HEAD
# Point CycloneDDS at the XML — needed on WiFi where multicast is flaky.
# The XML's <Peers> block must include every IP above. Set the path that
# matches the machine. The same file lives at the same path in every
# workspace because it is installed with the navigation package.
export CYCLONEDDS_URI="file://$HOME/ros2_ws/src/navigation/config/cyclone_dds.xml"
=======
# Avoid restricting ROS discovery to localhost during multi-robot testing.
# (Discovery range is set above per-domain.)
# CYCLONEDDS_URI is no longer used; domain isolation replaces the XML peer file.
unset CYCLONEDDS_URI
>>>>>>> 4410796 (Added topic bridges so only relevant topics are shared between robots improving battery life, tried to add slam positioning, implementing formation control)

# ── Hardware profile ──────────────────────────────────────────────────────────
export MACHINE_TYPE=MentorPi_Mecanum
export LIDAR_TYPE=LD19

echo "[setup_env] RMW=${RMW_IMPLEMENTATION}  DOMAIN=${ROS_DOMAIN_ID}  ROBOT=${ROBOT_NAME:-coordinator}"
echo "[setup_env] STATIC_PEERS=${ROS_STATIC_PEERS}"