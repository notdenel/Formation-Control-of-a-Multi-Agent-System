"""
infrastructure.launch.py
========================
Coordinator-side stack. Run this on the WSL laptop in domain 10.

  ros2 launch navigation infrastructure.launch.py

Starts:
  - map_server        (domain 10)
  - pose_aggregator   (domain 10, subscribes /robotX/amcl_pose)
  - rviz2             (optional, domain 10)

Domain bridging is NOT done here — each robot runs its own odom_bridge
(odom_bridge.launch.py) to relay /robotX/odom into domain 10.
cmd_vel stays entirely within each robot's private domain; aggregation
runs on-robot and publishes locally.
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, TimerAction
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    pkg_dir  = get_package_share_directory('navigation')
    map_yaml = os.path.join(pkg_dir, 'config', 'maps', 'map_01.yaml')
    rviz_cfg = os.path.join(pkg_dir, 'rviz', 'multi_robot.rviz')

    use_sim_time_arg = DeclareLaunchArgument('use_sim_time', default_value='false')
    rviz_arg = DeclareLaunchArgument(
        'rviz', default_value='false',
        description='Set true to open RViz (requires rviz2 installed — desktop only)')

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
        use_sim_time_arg,
        rviz_arg,
        map_server,
        map_lifecycle,
        pose_aggregator,
        TimerAction(period=2.0, actions=[rviz]),
    ])