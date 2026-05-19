"""
infrastructure.launch.py
========================
Shared base: map_server + pose_aggregator.
Run this on the Pi.  RViz runs on your desktop (see below).

  ros2 launch navigation infrastructure.launch.py

Add robots in separate terminals:

  Fake robot (static, movable via RViz 2D Pose Estimate):
    ros2 run navigation robot_pose_broadcaster \\
        --ros-args -p robot_name:=robot1 -p x:=0.0 -p y:=0.0

  Fake robot (wandering circle):
    ros2 run navigation robot_pose_broadcaster \\
        --ros-args -p robot_name:=robot2 -p x:=2.0 -p wander:=true

  Real robot hardware:
    ros2 launch navigation real_robot.launch.py robot_name:=robot1

Move a fake robot from CLI:
    ros2 topic pub --once /robot2/initialpose \\
        geometry_msgs/PoseWithCovarianceStamped \\
        '{header:{frame_id: map}, pose:{pose:{position:{x: 1.5, y: 0.5}}}}'

RViz on desktop (WSL/laptop — same ROS_DOMAIN_ID as Pi):
  rviz2 -d <path>/navigation/rviz/multi_robot.rviz
  Fixed Frame: map  |  Add Map: /map  |  Add Pose: /robot1/amcl_pose etc.
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
        parameters=[{
            'robot_names':  ['robot1', 'robot2', 'robot3'],
            'use_sim_time': use_sim_time,
        }],
    )

    # rviz:=true only on a machine that has the rviz2 binary (not a headless Pi)
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
