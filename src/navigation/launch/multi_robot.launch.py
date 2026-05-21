"""
multi_robot.launch.py
=====================
All-fake demo: map + 3 odom broadcasters + aggregator.
No hardware required.

  ros2 launch navigation multi_robot.launch.py

Topics published:
  /map                 — occupancy grid
  /robot1/odom         — robot1 at (0, 0)
  /robot2/odom         — robot2 at (2, 0)
  /robot3/odom         — robot3 at (-2, 0)
  /global_robot_states — PoseArray, frame=odom

TF tree:
  robot1/odom → robot1/base_footprint → robot1/lidar_frame
  robot2/odom → robot2/base_footprint → robot2/lidar_frame
  robot3/odom → robot3/base_footprint → robot3/lidar_frame

Verify:
  ros2 topic list | grep -E 'odom|global'
  ros2 topic echo /global_robot_states --once
  ros2 run tf2_tools view_frames
"""

import math
import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, TimerAction
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

# [name, x, y, yaw_deg]
ROBOT_CONFIGS = [
    ('robot1',  0.0,  0.0, 0.0),
    ('robot2',  2.0,  0.0, 0.0),
    ('robot3', -2.0,  0.0, 0.0),
]


def generate_launch_description():
    pkg_dir  = get_package_share_directory('navigation')
    map_yaml = os.path.join(pkg_dir, 'config', 'maps', 'map_01.yaml')
    rviz_cfg = os.path.join(pkg_dir, 'rviz', 'multi_robot.rviz')

    use_sim_time_arg = DeclareLaunchArgument('use_sim_time', default_value='false')
    rviz_arg = DeclareLaunchArgument(
        'rviz', default_value='false',
        description='Set true to open RViz (desktop only — requires rviz2)')

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

    pose_broadcasters = [
        Node(
            package='navigation',
            executable='robot_pose_broadcaster',
            name=f'pose_broadcaster_{name}',
            output='screen',
            parameters=[{
                'robot_name': name,
                'x':          float(x),
                'y':          float(y),
                'yaw':        float(math.radians(yaw_deg)),
                'use_sim_time': use_sim_time,
            }],
        )
        for name, x, y, yaw_deg in ROBOT_CONFIGS
    ]

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
        *pose_broadcasters,
        pose_aggregator,
        TimerAction(period=2.0, actions=[rviz]),
    ])
