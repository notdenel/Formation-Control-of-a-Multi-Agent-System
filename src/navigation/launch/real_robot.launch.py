"""
real_robot.launch.py
====================
Full hardware stack for ONE physical robot, properly namespaced. Loads map.

  ros2 launch navigation real_robot.launch.py robot_name:=robot1
  ros2 launch navigation real_robot.launch.py robot_name:=robot2
  ros2 launch navigation real_robot.launch.py robot_name:=robot3

This file follows the same pattern as slam/launch/slam.launch.py — peripheral
launches (lidar, imu, odom, rf2o) are included from their owning packages and
all relative topics/frames are namespaced with PushRosNamespace at one place.

Stack started under namespace /robotX:
  lidar driver      → /robotX/scan_raw                 (reliable QoS)
  ros_robot_ctrl    → /robotX/ros_robot_controller/*   (hardware driver)
  odom_publisher    → /robotX/odom_raw                 (wheel encoder odometry)
  imu_filter        → /robotX/imu                      (fused complementary)
  rf2o              → /robotX/odom_rf2o                (laser-scan odometry)
  ekf_filter_node   → /robotX/odom                     (fused: wheel + rf2o + imu)
                      TF:  robotX/odom → robotX/base_footprint
  map_server        → /robotX/map                      (serves pre-built SLAM map)
  amcl              → /robotX/amcl_pose                (global localisation)
                      TF:  map → robotX/odom
  global_costmap    → /robotX/global_costmap/…         (merged obstacle grid)

TF tree on each robot (requires all robots connected via DDS):
  map
  ├── robot1/odom → robot1/base_footprint → robot1/lidar_frame
  ├── robot2/odom → robot2/base_footprint → robot2/lidar_frame
  └── robot3/odom → robot3/base_footprint → robot3/lidar_frame

DDS setup (must match on all robots):
  CycloneDDS with static peers — see config/cyclone_dds.xml

Set initial pose after launch (replace x/y with robot's known starting position):
    ros2 topic pub --once /robot1/initialpose \
    geometry_msgs/msg/PoseWithCovarianceStamped \
    '{header: {frame_id: map}, pose: {pose: {position: {x: 0.0, y: 0.0, z: 0.0}, orientation: {w: 1.0}}}}'
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument, GroupAction, IncludeLaunchDescription,
    OpaqueFunction, SetEnvironmentVariable, TimerAction,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node, PushRosNamespace
from nav2_common.launch import ReplaceString


# Single source of truth for topic names shared between lidar, rf2o, EKF and AMCL.
# Matches the convention used in slam/launch/slam.launch.py.
_ODOM_TOPIC = 'odom_rf2o'
_SCAN_TOPIC = 'scan_raw'


def launch_setup(context, *args, **kwargs):
    robot_name        = LaunchConfiguration('robot_name').perform(context)
    map_name          = LaunchConfiguration('map').perform(context)
    use_sim_time      = LaunchConfiguration('use_sim_time').perform(context)
    use_sim_time_bool = use_sim_time.lower() == 'true'

    pkg_nav  = get_package_share_directory('navigation')
    pkg_periph = get_package_share_directory('peripherals')
    pkg_ctrl   = get_package_share_directory('controller')
    pkg_rf2o   = get_package_share_directory('rf2o_laser_odometry')

    lidar_launch    = os.path.join(pkg_periph, 'launch', 'lidar.launch.py')
    odom_pub_launch = os.path.join(pkg_ctrl,   'launch', 'odom_publisher.launch.py')
    rf2o_launch     = os.path.join(pkg_rf2o,   'launch', 'rf2o_laser_odometry.launch.py')
    single_launch   = os.path.join(pkg_nav,  'launch', 'single_robot.launch.py')
    costmap_params  = os.path.join(pkg_nav,  'config', 'multi_robot_costmap.yaml')

    # Fully-qualified frame IDs. ROS frame IDs are NEVER auto-namespaced by
    # PushRosNamespace — they must be passed explicitly.
    odom_frame  = f'{robot_name}/odom'
    base_frame  = f'{robot_name}/base_footprint'
    imu_frame   = f'{robot_name}/imu_link'
    lidar_frame = f'{robot_name}/lidar_frame'

    # EKF parameters: controller/config/ekf.yaml uses 'namespace/' as a literal
    # placeholder; rewrite it to 'robotX/' so frame IDs become fully qualified.
    ekf_param = ReplaceString(
        source_file=os.path.join(pkg_ctrl, 'config', 'ekf.yaml'),
        replacements={'namespace/': f'{robot_name}/'},
    )

    # ── Lidar driver ──────────────────────────────────────────────────────────
    # Publishes /{robot_name}/scan_raw at reliable QoS (LD19 default). The
    # laser_filters chain is disabled in lidar.launch.py, so 'scan' is never
    # produced — every consumer (rf2o, AMCL, costmap) subscribes to scan_raw.
    lidar = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(lidar_launch),
        launch_arguments={
            'scan_raw':    _SCAN_TOPIC,
            'lidar_frame': lidar_frame,
        }.items(),
    )

    # ── Hardware driver + wheel-encoder odometry ──────────────────────────────
    # use_namespace='false' because the outer GroupAction below already pushes
    # /{robot_name}; we MUST NOT double-namespace.
    #
    # Inside /{robot_name} this gives:
    #   /{robot_name}/ros_robot_controller/imu_raw      (raw IMU from MCU)
    #   /{robot_name}/ros_robot_controller/set_motor    (motor command sink)
    #   /{robot_name}/odom_raw                          (wheel-encoder odometry)
    #   /{robot_name}/controller/cmd_vel                (cmd_vel sink)
    odom_pub = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(odom_pub_launch),
        launch_arguments={
            'namespace':     '',
            'use_namespace': 'false',
            'odom_frame':    odom_frame,
            'base_frame':    base_frame,
            'imu_frame':     imu_frame,
            'cmd_vel_topic': 'controller/cmd_vel',
        }.items(),
    )

    # ── IMU complementary filter ──────────────────────────────────────────────
    # peripherals/imu_filter.launch.py hard-codes the absolute path
    # /ros_robot_controller/imu_raw — that breaks under PushRosNamespace
    # because the hardware driver publishes to /{robot_name}/ros_robot_controller/imu_raw.
    # We re-instantiate the complementary filter here with absolute paths
    # rewritten to the namespaced topic, and a relative output 'imu' so it
    # resolves to /{robot_name}/imu (which is what EKF subscribes to).
    imu_filter = TimerAction(
        period=3.0,
        actions=[Node(
            package='imu_complementary_filter',
            executable='complementary_filter_node',
            name='imu_filter',
            output='screen',
            parameters=[{
                'use_mag':              False,
                'do_bias_estimation':   True,
                'do_adaptive_gain':     True,
                'publish_debug_topics': False,
                'use_sim_time':         use_sim_time_bool,
            }],
            remappings=[
                # Absolute path → must point at the namespaced hardware topic.
                ('/imu/data_raw', f'/{robot_name}/ros_robot_controller/imu_raw'),
                # Relative output → /{robot_name}/imu inside the namespace.
                ('imu/data', 'imu'),
            ],
        )],
    )

    # ── rf2o laser odometry ───────────────────────────────────────────────────
    # rf2o_laser_odometry.launch.py declares laser_scan_topic_qos='reliable' to
    # match the LD19 publisher. Subscribes /{robot_name}/scan_raw, publishes
    # /{robot_name}/odom_rf2o (consumed by EKF as odom1).
    rf2o = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(rf2o_launch),
        launch_arguments={
            'scan_raw':      _SCAN_TOPIC,
            'odom_topic':    _ODOM_TOPIC,
            'base_frame_id': base_frame,
            'odom_frame_id': odom_frame,
        }.items(),
    )

    # ── Static TF: base_footprint → imu_link ──────────────────────────────────
    # The IMU driver stamps messages with frame_id={robot_name}/imu_link.
    # Without this TF, EKF would reject every imu0 message ("Could not obtain
    # transform"). Mounted at zero offset on this chassis — adjust if relevant.
    imu_static_tf = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='imu_static_tf',
        output='screen',
        arguments=[
            '--x', '0.0', '--y', '0.0', '--z', '0.0',
            '--roll', '0.0', '--pitch', '0.0', '--yaw', '0.0',
            '--frame-id', base_frame,
            '--child-frame-id', imu_frame,
        ],
    )

    # ── EKF: fuses /odom_raw + /odom_rf2o + /imu ──────────────────────────────
    # Publishes /{robot_name}/odom and the TF {robot_name}/odom → {robot_name}/base_footprint.
    # No /tf remap: every robot writes to the global /tf so the costmap can see
    # all robots' transforms via shared DDS discovery.
    ekf = Node(
        package='robot_localization',
        executable='ekf_node',
        name='ekf_filter_node',
        output='screen',
        parameters=[ekf_param, {'use_sim_time': use_sim_time_bool}],
        remappings=[('odometry/filtered', 'odom')],
    )

    # ── Pose normalizer ───────────────────────────────────────────────────────
    # Three position sources in the map frame, all at /{robot_name}/*:
    #   position   ← AMCL (authoritative global localisation)
    #   tf_pose    ← TF lookup map → base_footprint at 10 Hz
    #   odom_pose  ← EKF odom projected into map via TF
    pose_norm = Node(
        package='navigation',
        executable='pose_normalizer',
        name='pose_normalizer',
        output='screen',
        parameters=[{
            'robot_name':   robot_name,
            'use_sim_time': use_sim_time_bool,
        }],
    )

    # All robot-local nodes share a single namespace push.
    # PushRosNamespace applies to:
    #   - Relative topic names (scan_raw, odom_raw, imu, …)
    #   - Node names (so the node graph shows /robot1/ekf_filter_node, etc.)
    # It does NOT touch frame IDs or absolute topic paths — those are passed
    # explicitly above.
    bringup_group = GroupAction([
        PushRosNamespace(robot_name),
        lidar,
        odom_pub,
        imu_filter,
        imu_static_tf,
        rf2o,
        ekf,
        pose_norm,
    ])

    # ── AMCL + map_server ─────────────────────────────────────────────────────
    # single_robot.launch.py owns its own PushRosNamespace and frame qualification.
    # Kept outside bringup_group so we never accidentally double-namespace.
    localization = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(single_launch),
        launch_arguments={
            'robot_name':   robot_name,
            'use_sim_time': use_sim_time,
            'map':          map_name,
            'scan_topic':   _SCAN_TOPIC,
        }.items(),
    )

    # ── Shared global costmap ─────────────────────────────────────────────────
    # One instance per robot; each subscribes to /robot1/scan_raw, /robot2/scan_raw,
    # /robot3/scan_raw via absolute paths in multi_robot_costmap.yaml. The shared
    # /tf stream lets every scan land in the map frame regardless of source robot.
    # Delayed 15 s so AMCL has published map → odom before costmap configures.
    costmap_group = GroupAction([
        PushRosNamespace(robot_name),
        Node(
            package='nav2_costmap_2d',
            executable='nav2_costmap_2d',
            name='global_costmap',
            output='screen',
            parameters=[costmap_params, {
                'use_sim_time':     use_sim_time_bool,
                'robot_base_frame': base_frame,
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
                'bond_timeout': 0.0,
            }],
        ),
    ])
    delayed_costmap = TimerAction(period=15.0, actions=[costmap_group])

    return [bringup_group, localization, delayed_costmap]


def generate_launch_description():
    pkg_multi = get_package_share_directory('navigation')
    dds_cfg   = os.path.join(pkg_multi, 'config', 'cyclone_dds.xml')

    return LaunchDescription([
        # DDS static peer discovery — must be set before any ROS2 node starts.
        SetEnvironmentVariable('RMW_IMPLEMENTATION', 'rmw_cyclonedds_cpp'),
        SetEnvironmentVariable('CYCLONEDDS_URI',     dds_cfg),

        DeclareLaunchArgument('map', default_value='map_01'),
        DeclareLaunchArgument(
            'robot_name', default_value='robot1',
            description='Robot namespace — robot1 | robot2 | robot3'),
        DeclareLaunchArgument(
            'use_sim_time', default_value='false'),

        OpaqueFunction(function=launch_setup),
    ])
