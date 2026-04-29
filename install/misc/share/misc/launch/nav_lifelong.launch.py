"""
nav_lifelong.launch.py
======================
Phase 2 — Lifelong mapping + autonomous navigation using global_ref_nav and center_of_mass.

Loads a previously saved map (.posegraph from slam_toolbox) and runs:
  1. LiDAR driver
  2. Robot controller (odom + EKF + IMU)
  3. Static TF  base_footprint → lidar_frame
  4. slam_toolbox lifelong_slam_toolbox_node  — localises AND keeps updating map
  5. slam_pose_relay  — converts slam_toolbox TF → /amcl_pose for global_ref_nav
  6. global_ref_nav   — APF-based motion with CoM following and AMCL localisation
  7. center_of_mass   — shared CoM publisher / trigger

Usage
-----
  source ~/ros2_ws/setup_env.sh
  ros2 launch misc nav_lifelong.launch.py \
      map_file:=/home/agent3/ros2_ws/src/misc/maps/my_map

  # Set a new center-of-mass target (map frame, metres):
  ros2 service call /center_of_mass/set_position interfaces/srv/SetPose2D \
      "{data: {x: 1.5, y: 0.8, theta: 0.0}}"

  # Trigger all agents to move to CoM:
  ros2 service call /center_of_mass/trigger_move std_srvs/srv/Trigger "{}"

  # Cancel movement:
  ros2 topic pub --once /center_of_mass/cancel std_msgs/msg/Empty "{}"

Notes
-----
  - map_file must be the path WITHOUT extension.
    e.g. if you saved to ~/ros2_ws/src/misc/maps/my_map, pass
    map_file:=<absolute-path>/my_map  (no .posegraph suffix).

  - global_ref_nav subscribes to /imu_corrected; it is remapped to /imu here
    (the complementary_filter_node output topic).

  - rf2o_laser_odometry is not launched (package not installed); global_ref_nav
    falls back to AMCL (from slam_pose_relay) + IMU.
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription, LaunchService
from launch.actions import (DeclareLaunchArgument, IncludeLaunchDescription,
                             TimerAction)
from launch.substitutions import LaunchConfiguration
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node


def generate_launch_description():
    misc_pkg        = get_package_share_directory('misc')
    controller_pkg  = get_package_share_directory('controller')
    peripherals_pkg = get_package_share_directory('peripherals')

    default_map = os.path.join(misc_pkg, 'maps/my_map')

    # ── Arguments ────────────────────────────────────────────────────────────
    map_file_arg = DeclareLaunchArgument(
        'map_file', default_value=default_map,
        description='Full path to saved .posegraph map (no extension)')

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

    # ── 2. Controller ─────────────────────────────────────────────────────────
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

    # ── 4. slam_toolbox lifelong mode ─────────────────────────────────────────
    lifelong_slam_node = Node(
        package='slam_toolbox',
        executable='lifelong_slam_toolbox_node',
        name='slam_toolbox',
        output='screen',
        parameters=[
            os.path.join(misc_pkg, 'config/mapper_params_lifelong.yaml'),
            {'map_file_name': LaunchConfiguration('map_file')},
        ],
    )

    # ── 5. slam_pose_relay ───────────────────────────────────────────────────
    slam_pose_relay_node = Node(
        package='misc',
        executable='slam_pose_relay',
        name='slam_pose_relay',
        output='screen',
    )

    # ── 6. global_ref_nav ────────────────────────────────────────────────────
    # Remap /imu_corrected → /imu (complementary_filter_node output).
    global_ref_nav_node = Node(
        package='misc',
        executable='global_ref_nav',
        name='global_ref_nav',
        output='screen',
        remappings=[('/imu_corrected', '/imu')],
    )

    # ── 7. center_of_mass ────────────────────────────────────────────────────
    center_of_mass_node = Node(
        package='misc',
        executable='center_of_mass',
        name='center_of_mass',
        output='screen',
    )

    return LaunchDescription([
        map_file_arg,
        lidar_frame_arg,
        lidar_launch,
        controller_launch,
        static_tf_node,
        TimerAction(period=2.0, actions=[lifelong_slam_node]),
        TimerAction(period=5.0, actions=[
            slam_pose_relay_node,
            global_ref_nav_node,
            center_of_mass_node,
        ]),
    ])


if __name__ == '__main__':
    ld = generate_launch_description()
    ls = LaunchService()
    ls.include_launch_description(ld)
    ls.run()
