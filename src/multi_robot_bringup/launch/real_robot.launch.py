"""
real_robot.launch.py
====================
Full hardware stack for ONE physical robot, properly namespaced.

  ros2 launch multi_robot_bringup real_robot.launch.py robot_name:=robot1
  ros2 launch multi_robot_bringup real_robot.launch.py robot_name:=robot2
  ros2 launch multi_robot_bringup real_robot.launch.py robot_name:=robot3

Replaces all four previous bringup commands:
  ros2 launch controller controller.launch.py
  ros2 launch peripherals lidar.launch.py
  ros2 launch rf2o_laser_odometry rf2o_laser_odometry.launch.py
  ros2 launch slam slam_mapping.launch.py   ← replaced by AMCL localization

Stack started under namespace /robotX:
  lidar driver      → /robotX/scan_raw  /robotX/scan
  odom_publisher    → /robotX/odom_raw          (wheel encoder odometry)
  rf2o              → /robotX/odom_rf2o         (laser-scan odometry)
  ekf_filter_node   → /robotX/odom              (fused: wheel + rf2o + IMU)
                      TF:  robotX/odom → robotX/base_footprint
  map_server        → /robotX/map               (serves pre-built SLAM map)
  amcl              → /robotX/amcl_pose         (global localisation)
                      TF:  map → robotX/odom
  global_costmap    → /robotX/global_costmap/…  (merged obstacle grid, all robots)

TF tree on each robot (requires all 3 robots connected via DDS):
  map
  ├── robot1/odom → robot1/base_footprint → robot1/lidar_frame
  ├── robot2/odom → robot2/base_footprint → robot2/lidar_frame
  └── robot3/odom → robot3/base_footprint → robot3/lidar_frame

DDS setup (must match on all robots):
  CycloneDDS with static peers — see config/cyclone_dds.xml
  Source config/setup_env.sh, or set manually:
    export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
    export CYCLONEDDS_URI=~/ros2_ws/src/multi_robot_bringup/config/cyclone_dds.xml

Set initial pose after launch (replace x/y with robot's known starting position):
  ros2 topic pub --once /robot1/initialpose \\
      geometry_msgs/PoseWithCovarianceStamped \\
      '{header:{frame_id:map},pose:{pose:{position:{x:0.0,y:0.0}}}}'

Monitor all robot positions from any machine on the same DDS network:
  ros2 topic echo /global_robot_states
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

    pkg_multi  = get_package_share_directory('multi_robot_bringup')
    pkg_periph = get_package_share_directory('peripherals')
    pkg_ctrl   = get_package_share_directory('controller')

    lidar_launch    = os.path.join(pkg_periph, 'launch', 'lidar.launch.py')
    ctrl_launch     = os.path.join(pkg_ctrl,   'launch', 'controller.launch.py')
    single_launch   = os.path.join(pkg_multi,  'launch', 'single_robot.launch.py')
    costmap_params  = os.path.join(pkg_multi,  'config', 'multi_robot_costmap.yaml')

    # ── Lidar driver ──────────────────────────────────────────────────────────
    # Publishes: /{robot_name}/scan_raw   (raw, unfiltered)
    #            /{robot_name}/scan       (filtered, used by AMCL and rf2o)
    lidar_group = GroupAction([
        PushRosNamespace(robot_name),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(lidar_launch),
            launch_arguments={
                'scan_raw':    'scan_raw',
                'lidar_frame': f'{robot_name}/lidar_frame',
            }.items(),
        ),
    ])

    # ── Controller: wheel odom publisher + IMU filter + EKF ──────────────────
    # EKF fuses odom_raw (wheels) + odom_rf2o (laser) + imu.
    # Publishes:  /{robot_name}/odom
    # TF:         {robot_name}/odom → {robot_name}/base_footprint
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
    # The package's own launch file uses hardcoded absolute topics that break
    # multi-robot namespacing, so we inline the node here with correct params.
    #
    # Subscribes: /{robot_name}/scan_raw
    # Publishes:  /{robot_name}/odom_rf2o  (consumed by EKF as odom1)
    # publish_tf is false — EKF owns the odom→base_footprint transform.
    rf2o = Node(
        package='rf2o_laser_odometry',
        executable='rf2o_laser_odometry_node',
        name='rf2o_laser_odometry',
        output='screen',
        arguments=['--ros-args', '--log-level', 'WARN'],
        parameters=[{
            'laser_scan_topic':  f'/{robot_name}/scan_raw',
            'odom_topic':        f'/{robot_name}/odom_rf2o',
            'publish_tf':        False,
            'base_frame_id':     f'{robot_name}/base_footprint',
            'odom_frame_id':     f'{robot_name}/odom',
            'init_pose_from_topic': '',
            'freq':              10.0,
            'use_sim_time':      use_sim_time_bool,
        }],
    )

    # ── AMCL localization + map_server ────────────────────────────────────────
    # Publishes:  /{robot_name}/amcl_pose  (PoseWithCovarianceStamped)
    # TF:         map → {robot_name}/odom
    localization = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(single_launch),
        launch_arguments={
            'robot_name':   robot_name,
            'use_sim_time': use_sim_time,
        }.items(),
    )

    # ── Pose normalizer ───────────────────────────────────────────────────────
    # Three independently-sourced position topics in the map frame:
    #   /{robot_name}/position   ← AMCL  (authoritative global localization)
    #   /{robot_name}/tf_pose    ← TF lookup map→base_footprint (10 Hz)
    #   /{robot_name}/odom_pose  ← EKF odom projected into map via TF
    #
    # Gap between position and odom_pose = accumulated dead-reckoning drift
    # that AMCL is correcting.  All three should agree when localization is good.
    pose_norm_group = GroupAction([
        PushRosNamespace(robot_name),
        Node(
            package='multi_robot_bringup',
            executable='pose_normalizer',
            name='pose_normalizer',
            output='screen',
            parameters=[{
                'robot_name':   robot_name,
                'use_sim_time': use_sim_time_bool,
            }],
        ),
    ])

    # ── Shared global costmap ─────────────────────────────────────────────────
    # One instance per robot, all subscribing to /robot1/scan, /robot2/scan,
    # /robot3/scan. TF from the DDS-shared /tf stream places every scan
    # correctly in the map frame.
    # Publishes: /{robot_name}/global_costmap/costmap
    costmap_group = GroupAction([
        PushRosNamespace(robot_name),
        Node(
            package='nav2_costmap_2d',
            executable='nav2_costmap_2d',
            name='global_costmap',
            output='screen',
            parameters=[costmap_params, {
                'use_sim_time': use_sim_time_bool,
                # Override placeholder; must be fully qualified for TF lookups
                'robot_base_frame': f'{robot_name}/base_footprint',
            }],
        ),
        Node(
            package='nav2_lifecycle_manager',
            executable='lifecycle_manager',
            name='lifecycle_manager_costmap',
            output='screen',
            parameters=[{
                'use_sim_time': use_sim_time_bool,
                'autostart':    True,
                'node_names':   ['global_costmap'],
                'bond_timeout': 4.0,
            }],
        ),
    ])

    return [lidar_group, controller, rf2o, localization, pose_norm_group, costmap_group]


def generate_launch_description():
    pkg_multi   = get_package_share_directory('multi_robot_bringup')
    dds_cfg     = os.path.join(pkg_multi, 'config', 'cyclone_dds.xml')

    return LaunchDescription([
        # DDS static peer discovery — must be set before any ROS2 node starts
        SetEnvironmentVariable('RMW_IMPLEMENTATION',  'rmw_cyclonedds_cpp'),
        SetEnvironmentVariable('CYCLONEDDS_URI',       dds_cfg),

        DeclareLaunchArgument(
            'robot_name', default_value='robot1',
            description='Robot namespace — robot1 | robot2 | robot3'),
        DeclareLaunchArgument(
            'use_sim_time', default_value='false'),

        OpaqueFunction(function=launch_setup),
    ])
