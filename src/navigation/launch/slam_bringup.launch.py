"""
slam_bringup.launch.py
======================
Single-command SLAM mapping stack for ONE robot.  Equivalent to running:

  ros2 launch controller controller.launch.py             namespace:=robot1
  ros2 launch peripherals lidar.launch.py                 namespace:=robot1
  ros2 launch rf2o_laser_odometry rf2o_laser_odometry.launch.py namespace:=robot1
  ros2 launch slam slam_mapping.launch.py                 namespace:=robot1

Usage:

  ros2 launch navigation slam_bringup.launch.py robot_name:=robot1

Drive while mapping (separate terminal):

  ros2 run peripherals teleop_key_control --ros-args -r __ns:=/robot1

Save the map when done:

  ros2 service call /robot1/map_save_node/save_map std_srvs/srv/Trigger

Map is written to ~/ros2_ws/src/slam/maps/map_01.{pgm,yaml}.
Copy it to navigation/config/maps/ before running real_robot.launch.py.

EKF note
--------
real_robot.launch.py uses ekf.yaml with world_frame: map so the EKF fuses
AMCL pose corrections.  During SLAM mapping AMCL does not run and
slam_toolbox itself publishes map -> odom TF.  Running the EKF with
world_frame: map here would create a conflicting second map -> odom source.

Instead, the EKF runs with ekf_mapping.yaml (world_frame: odom), fusing
wheel encoder odometry, rf2o yaw, and IMU angular rate into a smooth
odom -> base_footprint TF.  slam_toolbox consumes that TF for its scan
matching and publishes map -> odom itself.  rf2o publish_tf is false.
"""

import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    OpaqueFunction,
    SetEnvironmentVariable,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def launch_setup(context, *args, **kwargs):
    robot_name   = LaunchConfiguration('robot_name').perform(context)
    use_sim_time = LaunchConfiguration('use_sim_time').perform(context)

    # Fully-qualified frame IDs — PushRosNamespace does not rewrite
    # header.frame_id fields so every frame must be explicit.
    odom_frame  = f'{robot_name}/odom'
    base_frame  = f'{robot_name}/base_footprint'
    imu_frame   = f'{robot_name}/imu_link'
    lidar_frame = f'{robot_name}/lidar_frame'

    pkg_ctrl  = get_package_share_directory('controller')
    pkg_per   = get_package_share_directory('peripherals')
    pkg_rf2o  = get_package_share_directory('rf2o_laser_odometry')
    pkg_slam  = get_package_share_directory('slam')

    # ── 1. Hardware driver + wheel encoder odom ───────────────────────────────
    # EKF runs with ekf_mapping.yaml (world_frame: odom).  slam_toolbox owns
    # the map→odom TF; the EKF owns odom→base_footprint, fusing wheel odom +
    # rf2o yaw + IMU angular rate.  rf2o publish_tf is therefore false.
    controller = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_ctrl, 'launch', 'controller.launch.py')),
        launch_arguments={
            'namespace':    robot_name,
            'use_sim_time': use_sim_time,
            'enable_odom':  'true',
            'ekf_config':   'ekf_mapping.yaml',
            'odom_frame':   odom_frame,
            'base_frame':   base_frame,
            'imu_frame':    imu_frame,
        }.items(),
    )

    # ── 2. Lidar driver + static base_footprint → lidar_frame TF ─────────────
    lidar = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_per, 'launch', 'lidar.launch.py')),
        launch_arguments={
            'namespace':   robot_name,
            'scan_raw':    'scan_raw',
            'lidar_frame': lidar_frame,
            'base_frame':  base_frame,
        }.items(),
    )

    # ── 3. RF2O laser odometry ────────────────────────────────────────────────
    # publish_tf: false — the EKF (ekf_mapping.yaml) owns the
    # odom → base_footprint TF.  rf2o provides odom_rf2o as a sensor input
    # to the EKF (yaw only) and slam_toolbox uses the EKF's TF.
    rf2o = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_rf2o, 'launch', 'rf2o_laser_odometry.launch.py')),
        launch_arguments={
            'namespace':     robot_name,
            'scan_raw':      f'/{robot_name}/scan_raw',
            'odom_topic':    f'/{robot_name}/odom_rf2o',
            'base_frame_id': base_frame,
            'odom_frame_id': odom_frame,
            'publish_tf':    'false',
            'freq':          '10.0',
        }.items(),
    )

    # ── 4. SLAM Toolbox (mapping) ─────────────────────────────────────────────
    slam = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_slam, 'launch', 'slam_mapping.launch.py')),
        launch_arguments={
            'namespace':    robot_name,
            'use_sim_time': use_sim_time,
        }.items(),
    )

    return [controller, lidar, rf2o, slam]


def generate_launch_description():
    return LaunchDescription([
        SetEnvironmentVariable('MACHINE_TYPE', 'MentorPi_Mecanum'),
        SetEnvironmentVariable('LIDAR_TYPE',   'LD19'),

        DeclareLaunchArgument(
            'robot_name',
            default_value='robot1',
            description='Robot namespace: robot1 | robot2 | robot3'),
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='false',
            description='Use simulation clock if true'),

        OpaqueFunction(function=launch_setup),
    ])
