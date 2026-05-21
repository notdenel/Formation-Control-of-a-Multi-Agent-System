"""
infrastructure.launch.py
========================
WSL coordinator stack: pose_aggregator + optional RViz.

Run this on the WSL laptop in ROS_DOMAIN_ID 10 (source setup_env.sh first):

  ros2 launch navigation infrastructure.launch.py

What this does:
  - Runs pose_aggregator which dynamically discovers active robots by watching
    for /robotX/odom publishers on domain 10.  Only robots whose odom bridge
    is running will appear — no phantom topics.

Domain bridging is NOT done here.  Each robot runs its own odom_bridge
(started by real_robot.launch.py) to relay /robotX/odom into domain 10.
cmd_vel stays entirely within each robot's private domain.

To verify robot positions from WSL:
  ros2 topic echo /robot1/odom         # EKF-fused odometry bridged from domain 11
  ros2 topic echo /global_robot_states # PoseArray from pose_aggregator
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, SetEnvironmentVariable
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    pkg_dir = get_package_share_directory('navigation')
    dds_cfg = os.path.join(pkg_dir, 'config', 'cyclone_dds.xml')

    use_sim_time_arg = DeclareLaunchArgument('use_sim_time', default_value='false')

    use_sim_time = LaunchConfiguration('use_sim_time')

    # Dynamic discovery: subscribes to /robotX/odom only when a live publisher
    # appears on domain 10.  Bridge ghost topics never emit messages, so only
    # running robots show up in /global_robot_states.
    pose_aggregator = Node(
        package='navigation',
        executable='pose_aggregator',
        name='pose_aggregator',
        output='screen',
        parameters=[{'use_sim_time': use_sim_time}],
    )

    return LaunchDescription([
        # WSL coordinator must be in domain 10 and use SUBNET discovery to reach
        # the robots' domain_bridge participants across WiFi.
        SetEnvironmentVariable('RMW_IMPLEMENTATION', 'rmw_cyclonedds_cpp'),
        SetEnvironmentVariable('CYCLONEDDS_URI', f'file://{dds_cfg}'),
        SetEnvironmentVariable('ROS_AUTOMATIC_DISCOVERY_RANGE', 'SUBNET'),

        use_sim_time_arg,
        pose_aggregator,
    ])
