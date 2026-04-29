"""
localization.launch.py
======================
AMCL localization on a static map (saved from slam_toolbox).

Brings up:
  1. LiDAR driver           -> /scan_raw
  2. Robot controller + EKF -> /odom, TF: odom -> base_footprint
  3. Static TF              base_footprint -> lidar_frame
  4. nav2_map_server        -> /map  (loads map_01.yaml)
  5. nav2_amcl              -> /amcl_pose, TF: map -> odom
  6. nav2 lifecycle_manager (auto-activates map_server + amcl)
  7. pose_printer           -> prints x,y to terminal

Usage
-----
  # build first:
  cd ~/ros2_ws && colcon build --symlink-install --packages-select misc
  source install/setup.bash

  # launch (uses slam/maps/map_01.yaml by default):
  ros2 launch misc localization.launch.py

  # to use a different map:
  ros2 launch misc localization.launch.py \
      map_yaml:=/home/agent3/ros2_ws/src/slam/maps/map_01.yaml

After launch, set the initial pose in RViz with the "2D Pose Estimate" tool,
or rely on the initial_pose block in amcl_params.yaml.

The robot's x,y in the map frame is published on:
  /amcl_pose   (geometry_msgs/PoseWithCovarianceStamped)
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction
from launch.substitutions import LaunchConfiguration
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node


def generate_launch_description():
    misc_pkg        = get_package_share_directory('misc')
    slam_pkg        = get_package_share_directory('slam')
    controller_pkg  = get_package_share_directory('controller')
    peripherals_pkg = get_package_share_directory('peripherals')

    default_map = os.path.join(slam_pkg, 'maps', 'map_01.yaml')
    amcl_yaml   = os.path.join(misc_pkg, 'config', 'amcl_params.yaml')

    # ── Arguments ────────────────────────────────────────────────────────────
    map_yaml_arg = DeclareLaunchArgument(
        'map_yaml', default_value=default_map,
        description='Full path to map .yaml file (saved from slam_toolbox)')

    use_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time', default_value='false')

    autostart_arg = DeclareLaunchArgument(
        'autostart', default_value='true',
        description='Auto-activate map_server + amcl lifecycle nodes')

    use_sim_time = LaunchConfiguration('use_sim_time')
    autostart    = LaunchConfiguration('autostart')
    map_yaml     = LaunchConfiguration('map_yaml')

    # ── 1. LiDAR ─────────────────────────────────────────────────────────────
    lidar_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(peripherals_pkg, 'launch/lidar.launch.py')),
        launch_arguments={
            'lidar_frame': 'lidar_frame',
            'scan_raw':    'scan_raw',
        }.items()
    )

    # ── 2. Controller + EKF (publishes odom -> base_footprint TF) ────────────
    controller_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(controller_pkg, 'launch/controller.launch.py')),
        launch_arguments={'enable_odom': 'true'}.items()
    )

    # ── 3. Static TF: base_footprint -> lidar_frame ──────────────────────────
    # Adjust z (and x/y/yaw) to match where your LiDAR is mounted on the robot.
    static_tf_node = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='lidar_tf',
        output='screen',
        arguments=[
            '--x', '0', '--y', '0', '--z', '0.10',
            '--roll', '0', '--pitch', '0', '--yaw', '0',
            '--frame-id', 'base_footprint',
            '--child-frame-id', 'lidar_frame',
        ],
    )

    # ── 4. Map server (lifecycle node) ───────────────────────────────────────
    map_server_node = Node(
        package='nav2_map_server',
        executable='map_server',
        name='map_server',
        output='screen',
        parameters=[{
            'use_sim_time': use_sim_time,
            'yaml_filename': map_yaml,
            'topic_name': 'map',
            'frame_id': 'map',
        }],
    )

    # ── 5. AMCL (lifecycle node) ─────────────────────────────────────────────
    amcl_node = Node(
        package='nav2_amcl',
        executable='amcl',
        name='amcl',
        output='screen',
        parameters=[amcl_yaml, {'use_sim_time': use_sim_time}],
    )

    # ── 6. Lifecycle manager — auto-configures + activates map_server, amcl ──
    lifecycle_mgr_node = Node(
        package='nav2_lifecycle_manager',
        executable='lifecycle_manager',
        name='lifecycle_manager_localization',
        output='screen',
        parameters=[{
            'use_sim_time': use_sim_time,
            'autostart':    autostart,
            'node_names':   ['map_server', 'amcl'],
            'bond_timeout': 0.0,
        }],
    )

    # ── 7. Pose printer (prints x,y from /amcl_pose) ─────────────────────────
    pose_printer_node = Node(
        package='misc',
        executable='pose_printer',
        name='pose_printer',
        output='screen',
    )

    return LaunchDescription([
        map_yaml_arg,
        use_sim_time_arg,
        autostart_arg,

        lidar_launch,
        controller_launch,
        static_tf_node,

        # Give controller + lidar a moment to come up before AMCL/map_server.
        TimerAction(period=3.0, actions=[map_server_node, amcl_node]),
        TimerAction(period=5.0, actions=[lifecycle_mgr_node]),
        TimerAction(period=7.0, actions=[pose_printer_node]),
    ])
