"""
real_robot.launch.py
====================
Full hardware stack for ONE physical robot, properly namespaced.
Replaces robot_pose_broadcaster for a robot with real sensors.

  # Terminal 1 — shared infrastructure
  ros2 launch multi_robot_bringup infrastructure.launch.py

  # Terminal 2 — this Pi's hardware
  ros2 launch multi_robot_bringup real_robot.launch.py robot_name:=robot1

Starts under namespace robotX:
  lidar driver      → /robotX/scan
  odom_publisher    → /robotX/odom_raw + TF robotX/odom→robotX/base_footprint
  ekf_node          → /robotX/odom (fused)
  map_server        → /robotX/map
  amcl              → /robotX/amcl_pose + TF map→robotX/odom
  lifecycle_manager → activates map_server + amcl

Set initial pose after launch:
  ros2 topic pub --once /robot1/initialpose \\
      geometry_msgs/PoseWithCovarianceStamped \\
      '{header:{frame_id:map},pose:{pose:{position:{x:0.0,y:0.0}}}}'

Requirements:
  LiDAR on /dev/ldlidar, controller board on /dev/ttyACM0
  MACHINE_TYPE and LIDAR_TYPE set (source ~/ros2_ws/src/misc/setup_env.sh)
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument, GroupAction, IncludeLaunchDescription, OpaqueFunction,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node, PushRosNamespace


def launch_setup(context, *args, **kwargs):
    robot_name   = LaunchConfiguration('robot_name').perform(context)
    use_sim_time = LaunchConfiguration('use_sim_time').perform(context)

    pkg_multi  = get_package_share_directory('multi_robot_bringup')
    pkg_periph = get_package_share_directory('peripherals')
    pkg_ctrl   = get_package_share_directory('controller')

    lidar_launch = os.path.join(pkg_periph, 'launch', 'lidar.launch.py')
    ctrl_launch  = os.path.join(pkg_ctrl,   'launch', 'controller.launch.py')
    single_launch = os.path.join(pkg_multi, 'launch', 'single_robot.launch.py')

    # ── Lidar wrapped in namespace ─────────────────────────────────────────────
    # scan_raw:=scan cancels the driver's internal remap so the driver publishes
    # 'scan', which PushRosNamespace expands to /robotX/scan.
    lidar_group = GroupAction([
        PushRosNamespace(robot_name),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(lidar_launch),
            launch_arguments={
                'scan_raw':    'scan',
                'lidar_frame': f'{robot_name}/lidar_frame',
            }.items(),
        ),
    ])

    # ── Controller / EKF (handles namespace internally via launch args) ────────
    controller = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(ctrl_launch),
        launch_arguments={
            'namespace':     robot_name,
            'use_namespace': 'true',
            'odom_frame':    f'{robot_name}/odom',
            'base_frame':    f'{robot_name}/base_footprint',
            'enable_odom':   'true',
            'use_sim_time':  use_sim_time,
        }.items(),
    )

    # ── AMCL + map_server ─────────────────────────────────────────────────────
    localization = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(single_launch),
        launch_arguments={
            'robot_name':   robot_name,
            'use_sim_time': use_sim_time,
        }.items(),
    )

    return [lidar_group, controller, localization]


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument(
            'robot_name', default_value='robot1',
            description='Robot namespace — must match nav2_params_robotX.yaml'),
        DeclareLaunchArgument(
            'use_sim_time', default_value='false'),
        OpaqueFunction(function=launch_setup),
    ])
