"""
slam_mapping.launch.py
======================
Phase 1 — Build a map using SLAM Toolbox (online async) with optional RViz.

What this launches:
  1. LiDAR driver      (LD06 via peripherals/lidar.launch.py)
  2. Robot controller  (odom + EKF + IMU via controller/controller.launch.py)
  3. Static TF         base_footprint → lidar_frame  (lidar mounting)
  4. slam_toolbox      async_slam_toolbox_node
  5. rviz2             only when use_rviz:=true  (requires ros-jazzy-rviz2)

Workflow
--------
  source ~/ros2_ws/setup_env.sh

  # Without RViz (headless robot):
  ros2 launch misc slam_mapping.launch.py

  # With RViz on this machine (needs: sudo apt install ros-jazzy-rviz2):
  ros2 launch misc slam_mapping.launch.py use_rviz:=true

  # With RViz on a separate workstation (same ROS_DOMAIN_ID):
  #   On workstation: rviz2 -d ~/ros2_ws/src/misc/rviz/slam_mapping.rviz

  # Drive the robot (new terminal):
  ros2 run peripherals teleop_key_control

  # Save map when done (saves .yaml + .pgm for nav2 AND .posegraph for lifelong):
  ros2 run nav2_map_server map_saver_cli -f ~/ros2_ws/src/misc/maps/my_map
  ros2 service call /slam_toolbox/save_map slam_toolbox/srv/SaveMap \
      "{name: {data: '/home/agent1/ros2_ws/src/misc/maps/my_map'}}"
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription, LaunchService
from launch.actions import (DeclareLaunchArgument, IncludeLaunchDescription,
                             TimerAction)
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node


def generate_launch_description():
    misc_pkg        = get_package_share_directory('misc')
    controller_pkg  = get_package_share_directory('controller')
    peripherals_pkg = get_package_share_directory('peripherals')

    # ── Arguments ────────────────────────────────────────────────────────────
    use_rviz_arg = DeclareLaunchArgument(
        'use_rviz', default_value='false',
        description='Launch rviz2 (requires ros-jazzy-rviz2 installed)')

    lidar_frame_arg = DeclareLaunchArgument(
        'lidar_frame', default_value='lidar_frame',
        description='TF frame id for the LiDAR sensor')

    # ── 1. LiDAR ─────────────────────────────────────────────────────────────
    lidar_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(peripherals_pkg, 'launch/lidar.launch.py')),
        launch_arguments={
            'lidar_frame': LaunchConfiguration('lidar_frame'),
            'scan_raw':    'scan_raw',
        }.items()
    )

    # ── 2. Controller (odom publisher + EKF + IMU filter) ────────────────────
    controller_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(controller_pkg, 'launch/controller.launch.py')),
        launch_arguments={
            'enable_odom': 'true',
        }.items()
    )

    # ── 3. Static TF: base_footprint → lidar_frame ───────────────────────────
    static_tf_node = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='lidar_tf',
        output='screen',
        arguments=[
            '--x', '0', '--y', '0', '--z', '0.10',
            '--roll', '0', '--pitch', '0', '--yaw', '0',
            '--frame-id', 'base_footprint',
            '--child-frame-id', LaunchConfiguration('lidar_frame'),
        ],
    )

    # ── 4. slam_toolbox — online async mapping ────────────────────────────────
    slam_node = Node(
        package='slam_toolbox',
        executable='async_slam_toolbox_node',
        name='slam_toolbox',
        output='screen',
        parameters=[
            os.path.join(misc_pkg, 'config/mapper_params_mapping.yaml'),
        ],
    )

    # ── 5. rviz2 ─────────────────────────────────────────────────────────────
    # Only started when use_rviz:=true.  IfCondition prevents any package
    # resolution from happening when the flag is false, so the launch does not
    # crash if ros-jazzy-rviz2 is not installed.
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', os.path.join(misc_pkg, 'rviz/slam_mapping.rviz')],
        output='screen',
        condition=IfCondition(LaunchConfiguration('use_rviz')),
    )

    return LaunchDescription([
        use_rviz_arg,
        lidar_frame_arg,
        lidar_launch,
        controller_launch,
        static_tf_node,
        TimerAction(period=2.0, actions=[slam_node]),
        # rviz2 delayed so the map and TF are ready before the display connects
        TimerAction(period=4.0, actions=[rviz_node]),
    ])


if __name__ == '__main__':
    ld = generate_launch_description()
    ls = LaunchService()
    ls.include_launch_description(ld)
    ls.run()
