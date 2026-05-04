"""
hardware_bringup.launch.py
==========================
Hardware-only stack for one robot: lidar + controller (EKF) + rf2o.
No map server, no AMCL — use this during SLAM map building or bench testing.

SLAM workflow (run each in a separate terminal):

  # 1. Hardware — publishes /robot1/scan_raw, /robot1/odom etc.
  ros2 launch navigation hardware_bringup.launch.py robot_name:=robot1

  # 2. SLAM toolbox — subscribes to the namespaced topics above
  ros2 launch slam slam_mapping.launch.py \\
      scan_topic:=/robot1/scan_raw \\
      odom_frame:=robot1/odom \\
      base_frame:=robot1/base_footprint

  # 3. Teleop — publishes /robot1/controller/cmd_vel (matches hardware namespace)
  ros2 launch peripherals teleop_key_control.launch.py robot_name:=robot1

Topic map after all three are running:
  /robot1/scan_raw            lidar driver     → SLAM toolbox + rf2o
  /robot1/odom_rf2o           rf2o             → EKF (odom1)
  /robot1/odom_raw            wheel odom       → EKF (odom0)
  /robot1/imu                 IMU              → EKF
  /robot1/odom                EKF output       → SLAM toolbox (odom source)
  /robot1/controller/cmd_vel  teleop           → odom_publisher (motor driver)
  TF: robot1/odom → robot1/base_footprint      EKF
  TF: robot1/base_footprint → robot1/lidar_frame  static (this launch)
  TF: map → robot1/odom                        SLAM toolbox

Why separate from real_robot.launch.py:
  SLAM builds the map — there is no map yet to load into AMCL.
  Once mapping is done, switch to real_robot.launch.py for AMCL navigation.
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument, GroupAction, IncludeLaunchDescription,
    OpaqueFunction, SetEnvironmentVariable,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node, PushRosNamespace


def launch_setup(context, *args, **kwargs):
    robot_name   = LaunchConfiguration('robot_name').perform(context)
    use_sim_time = LaunchConfiguration('use_sim_time').perform(context)
    use_sim_time_bool = use_sim_time.lower() == 'true'

    pkg_periph = get_package_share_directory('peripherals')
    pkg_ctrl   = get_package_share_directory('controller')

    lidar_launch = os.path.join(pkg_periph, 'launch', 'lidar.launch.py')
    ctrl_launch  = os.path.join(pkg_ctrl,   'launch', 'controller.launch.py')

    # ── Lidar driver ──────────────────────────────────────────────────────────
    # PushRosNamespace makes the relative 'scan_raw' topic resolve to
    # /robot1/scan_raw inside the group — same logic as real_robot.launch.py.
    lidar_group = GroupAction([
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(lidar_launch),
            launch_arguments={
                'robot_name':  robot_name,
                'scan_raw':    'scan_raw',
                'lidar_frame': f'{robot_name}/lidar_frame',
            }.items(),
        )
    ])

    # ── Controller: wheel odom + IMU filter + EKF ─────────────────────────────
    # Passes use_namespace=true so odom_publisher.launch.py wraps both
    # odom_publisher and ros_robot_controller in the robot namespace.
    # odom_publisher then subscribes to /robot1/controller/cmd_vel.
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

    # ── rf2o laser odometry ───────────────────────────────────────────────────
    # Inlined (not via its own launch file) to override the hardcoded absolute
    # topic names that break multi-robot namespacing.
    # Subscribes: /robot1/scan_raw   Publishes: /robot1/odom_rf2o
    rf2o = Node(
        package='rf2o_laser_odometry',
        executable='rf2o_laser_odometry_node',
        name='rf2o_laser_odometry',
        output='screen',
        arguments=['--ros-args', '--log-level', 'WARN'],
        parameters=[{
            'laser_scan_topic':     f'/{robot_name}/scan_raw',
            'odom_topic':           f'/{robot_name}/odom_rf2o',
            'publish_tf':           False,
            'base_frame_id':        f'{robot_name}/base_footprint',
            'odom_frame_id':        f'{robot_name}/odom',
            'init_pose_from_topic': '',
            'freq':                 10.0,
            'use_sim_time':         use_sim_time_bool,
        }],
    )

    # ── Static TF: base_footprint → lidar_frame ───────────────────────────────
    # SLAM toolbox needs this to place scans in the correct frame.
    # Adjust z (0.10 m) to match your actual lidar mounting height.
    static_lidar_tf = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='lidar_static_tf',
        output='screen',
        arguments=[
            '--x', '0.0', '--y', '0.0', '--z', '0.10',
            '--roll', '0.0', '--pitch', '0.0', '--yaw', '0.0',
            '--frame-id',       f'{robot_name}/base_footprint',
            '--child-frame-id', f'{robot_name}/lidar_frame',
        ],
    )

    return [lidar_group, controller, rf2o, static_lidar_tf]


def generate_launch_description():
    pkg_nav = get_package_share_directory('navigation')
    dds_cfg   = os.path.join(pkg_nav, 'config', 'cyclone_dds.xml')

    return LaunchDescription([
        SetEnvironmentVariable('RMW_IMPLEMENTATION', 'rmw_cyclonedds_cpp'),
        SetEnvironmentVariable('CYCLONEDDS_URI',      dds_cfg),

        DeclareLaunchArgument(
            'robot_name', default_value='robot1',
            description='Robot namespace — robot1 | robot2 | robot3'),
        DeclareLaunchArgument(
            'use_sim_time', default_value='false'),

        OpaqueFunction(function=launch_setup),
    ])
