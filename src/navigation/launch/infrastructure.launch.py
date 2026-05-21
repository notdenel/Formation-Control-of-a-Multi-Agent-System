"""
infrastructure.launch.py
========================
WSL coordinator stack: map_server + pose_aggregator + optional RViz.

Run this on the WSL laptop in ROS_DOMAIN_ID 10 (source setup_env.sh first):

  ros2 launch navigation infrastructure.launch.py
  ros2 launch navigation infrastructure.launch.py rviz:=true

What this does:
  - Serves the shared map on domain 10 so RViz and any domain-10 tools can
    visualise it.
  - Runs pose_aggregator which dynamically discovers active robots by watching
    for /robotX/amcl_pose publishers on domain 10.  Only robots whose odom
    bridge is running and whose AMCL is active will appear — no phantom topics.
  - Optionally opens RViz with the multi-robot configuration.

Domain bridging is NOT done here.  Each robot runs its own odom_bridge
(started by real_robot.launch.py) to relay /robotX/odom and /robotX/amcl_pose
into domain 10.  cmd_vel stays entirely within each robot's private domain.

To verify robot positions from WSL:
  ros2 topic echo /robot1/odom      # EKF-fused odometry bridged from domain 11
  ros2 topic echo /robot1/amcl_pose # AMCL global pose bridged from domain 11
  ros2 topic echo /global_robot_states  # PoseArray from pose_aggregator
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, SetEnvironmentVariable, TimerAction
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    pkg_dir = get_package_share_directory('navigation')
    map_yaml = os.path.join(pkg_dir, 'config', 'maps', 'map_01.yaml')
    rviz_cfg = os.path.join(pkg_dir, 'rviz', 'multi_robot.rviz')
    dds_cfg = os.path.join(pkg_dir, 'config', 'cyclone_dds.xml')

    use_sim_time_arg = DeclareLaunchArgument('use_sim_time', default_value='false')
    rviz_arg = DeclareLaunchArgument(
        'rviz', default_value='false',
        description='Set true to open RViz (desktop/WSL only)')

    use_sim_time = LaunchConfiguration('use_sim_time')
    rviz_enabled = LaunchConfiguration('rviz')

    map_server = Node(
        package='nav2_map_server',
        executable='map_server',
        name='map_server',
        output='screen',
        parameters=[{
            'yaml_filename': map_yaml,
            'topic_name':    'map',
            'frame_id':      'map',
            'use_sim_time':  use_sim_time,
        }],
    )

    map_lifecycle = Node(
        package='nav2_lifecycle_manager',
        executable='lifecycle_manager',
        name='lifecycle_manager_map',
        output='screen',
        parameters=[{
            'autostart':    True,
            'node_names':   ['map_server'],
            'bond_timeout': 4.0,
            'use_sim_time': use_sim_time,
        }],
    )

    # Dynamic discovery: subscribes to /robotX/amcl_pose only when a live
    # publisher appears on domain 10.  Bridge ghost topics never emit messages,
    # so only running robots show up in /global_robot_states.
    pose_aggregator = Node(
        package='navigation',
        executable='pose_aggregator',
        name='pose_aggregator',
        output='screen',
        parameters=[{'use_sim_time': use_sim_time}],
    )

    rviz = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', rviz_cfg],
        output='screen',
        condition=IfCondition(rviz_enabled),
    )

    return LaunchDescription([
        # WSL coordinator must be in domain 10 and use SUBNET discovery to reach
        # the robots' domain_bridge participants across WiFi.
        SetEnvironmentVariable('RMW_IMPLEMENTATION', 'rmw_cyclonedds_cpp'),
        SetEnvironmentVariable('CYCLONEDDS_URI', f'file://{dds_cfg}'),
        SetEnvironmentVariable('ROS_AUTOMATIC_DISCOVERY_RANGE', 'SUBNET'),

        use_sim_time_arg,
        rviz_arg,
        map_server,
        map_lifecycle,
        pose_aggregator,
        TimerAction(period=2.0, actions=[rviz]),
    ])
