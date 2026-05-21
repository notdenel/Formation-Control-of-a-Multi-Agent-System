"""
real_robot.launch.py
====================

Full hardware stack for ONE physical robot, properly namespaced.

Example usage:

  ros2 launch navigation real_robot.launch.py robot_name:=robot1
  ros2 launch navigation real_robot.launch.py robot_name:=robot2
  ros2 launch navigation real_robot.launch.py robot_name:=robot3

Optional costmap:

  ros2 launch navigation real_robot.launch.py robot_name:=robot1 launch_costmap:=true

Architecture:
  EKF 1  (controller/config/ekf.yaml, world_frame=odom)
    fuses odom_raw + odom_rf2o + IMU  →  /robotX/odom + TF odom→base_footprint

  EKF 2  (navigation/config/ekf_map.yaml, world_frame=map)
    fuses amcl_pose                   →  /robotX/odom_amcl + TF map→odom
    AMCL provides the highest-quality global correction; EKF 2 smooths it.

  AMCL   (single_robot.launch.py)
    tf_broadcast: false — EKF 2 owns the map→odom transform.
    set_initial_pose: true at (0,0,yaw=0) — no RViz 2D Pose Estimate needed.
    Robots are physically placed at the map origin before driving.

  odom_bridge  (odom_bridge.launch.py)
    domain_bridge bridges only /robotX/odom + /robotX/amcl_pose outbound and
    peer /robotY/odom + /robotZ/odom inbound.  Everything else (scan, TF, IMU)
    stays in the robot's private domain.

  aggregation  (navigation/aggregation.py, delayed 20 s)
    Runs on-robot in the private domain.  Discovers live peers by verifying
    actual odom message flow (liveness check filters bridge ghost topics).
    Publishes /robotX/controller/cmd_vel locally — no cmd_vel bridge needed.

DDS setup:

  Each robot runs in its own private domain:
    robot1 → ROS_DOMAIN_ID 11
    robot2 → ROS_DOMAIN_ID 12
    robot3 → ROS_DOMAIN_ID 13

  Private-domain nodes use LOCALHOST discovery (stays on-device).
  domain_bridge uses SUBNET discovery (reaches WSL/fleet domain 10).
  CycloneDDS static peers are in: navigation/config/cyclone_dds.xml

Expected robot-local topics:

  /robotX/scan_raw
  /robotX/odom_raw
  /robotX/odom_rf2o
  /robotX/odom          ← EKF 1 (odom world-frame)
  /robotX/odom_amcl     ← EKF 2 (map world-frame)
  /robotX/imu
  /robotX/amcl_pose
  /robotX/position
  /robotX/controller/cmd_vel

Expected TF tree:

  map
  └── [EKF 2] robotX/odom
               └── [EKF 1] robotX/base_footprint
                            └── robotX/lidar_frame
"""

import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    GroupAction,
    IncludeLaunchDescription,
    OpaqueFunction,
    SetEnvironmentVariable,
    TimerAction,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration

from launch_ros.actions import Node, PushRosNamespace

from nav2_common.launch import ReplaceString


_SCAN_TOPIC = 'scan_raw'
_RF2O_ODOM_TOPIC = 'odom_rf2o'

_ROBOT_DOMAINS = {
    'robot1': '11',
    'robot2': '12',
    'robot3': '13',
}


def launch_setup(context, *args, **kwargs):
    robot_name = LaunchConfiguration('robot_name').perform(context)
    map_name = LaunchConfiguration('map').perform(context)
    use_sim_time = LaunchConfiguration('use_sim_time').perform(context)
    launch_costmap = LaunchConfiguration('launch_costmap').perform(context)

    use_sim_time_bool = use_sim_time.lower() == 'true'
    launch_costmap_bool = launch_costmap.lower() == 'true'

    pkg_nav = get_package_share_directory('navigation')
    pkg_periph = get_package_share_directory('peripherals')
    pkg_ctrl = get_package_share_directory('controller')
    pkg_rf2o = get_package_share_directory('rf2o_laser_odometry')

    lidar_launch = os.path.join(pkg_periph, 'launch', 'lidar.launch.py')
    odom_pub_launch = os.path.join(pkg_ctrl, 'launch', 'odom_publisher.launch.py')
    rf2o_launch = os.path.join(pkg_rf2o, 'launch', 'rf2o_laser_odometry.launch.py')
    single_launch = os.path.join(pkg_nav, 'launch', 'single_robot.launch.py')
    odom_bridge_launch = os.path.join(pkg_nav, 'launch', 'odom_bridge.launch.py')
    costmap_params = os.path.join(pkg_nav, 'config', 'multi_robot_costmap.yaml')

    odom_frame = f'{robot_name}/odom'
    base_frame = f'{robot_name}/base_footprint'
    imu_frame = f'{robot_name}/imu_link'
    lidar_frame = f'{robot_name}/lidar_frame'

    # EKF 1: fuses wheel encoder + RF2O + IMU → odom world-frame.
    ekf_param = ReplaceString(
        source_file=os.path.join(pkg_ctrl, 'config', 'ekf.yaml'),
        replacements={'namespace/': f'{robot_name}/'},
    )

    # EKF 2: fuses AMCL pose → map world-frame, publishes map→odom TF.
    ekf_map_param = ReplaceString(
        source_file=os.path.join(pkg_nav, 'config', 'ekf_map.yaml'),
        replacements={'namespace/': f'{robot_name}/'},
    )

    lidar = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(lidar_launch),
        launch_arguments={
            'scan_raw': _SCAN_TOPIC,
            'lidar_frame': lidar_frame,
            'base_frame': base_frame,
        }.items(),
    )

    odom_pub = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(odom_pub_launch),
        launch_arguments={
            'namespace': '',
            'use_namespace': 'false',
            'odom_frame': odom_frame,
            'base_frame': base_frame,
            'imu_frame': imu_frame,
            'cmd_vel_topic': 'controller/cmd_vel',
        }.items(),
    )

    imu_filter = TimerAction(
        period=3.0,
        actions=[
            Node(
                package='imu_complementary_filter',
                executable='complementary_filter_node',
                name='imu_filter',
                output='screen',
                parameters=[{
                    'use_mag': False,
                    'do_bias_estimation': True,
                    'do_adaptive_gain': True,
                    'publish_debug_topics': False,
                    'use_sim_time': use_sim_time_bool,
                }],
                remappings=[
                    ('imu/data_raw', f'/{robot_name}/ros_robot_controller/imu_raw'),
                    ('imu/data', 'imu'),
                ],
            )
        ],
    )

    rf2o = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(rf2o_launch),
        launch_arguments={
            'scan_raw': _SCAN_TOPIC,
            'odom_topic': _RF2O_ODOM_TOPIC,
            'base_frame_id': base_frame,
            'odom_frame_id': odom_frame,
            'publish_tf': 'false',
            'freq': '8.0',
        }.items(),
    )

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

    # EKF 1: odom world-frame — dead-reckoning.
    ekf_odom = Node(
        package='robot_localization',
        executable='ekf_node',
        name='ekf_filter_node',
        output='screen',
        parameters=[ekf_param, {'use_sim_time': use_sim_time_bool}],
        remappings=[('odometry/filtered', 'odom')],
    )

    # EKF 2: map world-frame — AMCL-based global correction.
    # Delayed until AMCL has converged and begun publishing amcl_pose.
    # AMCL starts with set_initial_pose so it should be active within ~5 s
    # of the lifecycle manager activating it; 10 s delay gives ample margin.
    ekf_map = TimerAction(
        period=10.0,
        actions=[Node(
            package='robot_localization',
            executable='ekf_node',
            name='ekf_global_filter_node',
            output='screen',
            parameters=[ekf_map_param, {'use_sim_time': use_sim_time_bool}],
            remappings=[('odometry/filtered', 'odom_amcl')],
        )],
    )

    pose_norm = Node(
        package='navigation',
        executable='pose_normalizer',
        name='pose_normalizer',
        output='screen',
        parameters=[{
            'robot_name': robot_name,
            'use_sim_time': use_sim_time_bool,
        }],
    )

    bringup_group = GroupAction([
        PushRosNamespace(robot_name),
        lidar,
        odom_pub,
        imu_filter,
        imu_static_tf,
        rf2o,
        ekf_odom,
        ekf_map,
        pose_norm,
    ])

    # AMCL + map server (single_robot.launch.py manages its own namespace).
    # AMCL has tf_broadcast: false in nav2_params; EKF 2 owns map→odom TF.
    localization = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(single_launch),
        launch_arguments={
            'robot_name': robot_name,
            'use_sim_time': use_sim_time,
            'map': map_name,
            'scan_topic': _SCAN_TOPIC,
        }.items(),
    )

    # odom_bridge: bridges /robotX/odom and /robotX/amcl_pose to fleet domain
    # 10, and brings peer odom topics into this robot's private domain.
    odom_bridge = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(odom_bridge_launch),
        launch_arguments={'robot_name': robot_name}.items(),
    )

    # Aggregation: discovers live peers by checking for actual odom messages
    # (not just topic existence) to avoid acting on bridge ghost topics.
    # Delayed 20 s: EKF must be publishing odom and odom_bridge must have
    # connected to domain 10 before peer odom topics start flowing.
    aggregation = TimerAction(
        period=20.0,
        actions=[Node(
            package='navigation',
            executable='aggregation',
            name='aggregation',
            output='screen',
            parameters=[{'use_sim_time': use_sim_time_bool}],
        )],
    )

    actions = [
        bringup_group,
        localization,
        odom_bridge,
        aggregation,
    ]

    if launch_costmap_bool:
        costmap_group = GroupAction([
            PushRosNamespace(robot_name),
            Node(
                package='nav2_costmap_2d',
                executable='nav2_costmap_2d',
                name='global_costmap',
                output='screen',
                parameters=[
                    costmap_params,
                    {
                        'use_sim_time': use_sim_time_bool,
                        'robot_base_frame': base_frame,
                    },
                ],
            ),
            Node(
                package='nav2_lifecycle_manager',
                executable='lifecycle_manager',
                name='lifecycle_manager_costmap',
                output='screen',
                parameters=[{
                    'use_sim_time': use_sim_time_bool,
                    'autostart': True,
                    'node_names': ['global_costmap'],
                    'bond_timeout': 0.0,
                }],
            ),
        ])
        actions.append(TimerAction(period=15.0, actions=[costmap_group]))

    return actions


def generate_launch_description():
    pkg_nav = get_package_share_directory('navigation')
    dds_cfg = os.path.join(pkg_nav, 'config', 'cyclone_dds.xml')

    return LaunchDescription([
        # Private domain per robot — inherited from setup_env.sh, but the
        # launch file sets the domain explicitly so it works even if the user
        # hasn't sourced setup_env.sh.  OpaqueFunction resolves robot_name
        # after these environment actions, so we must set all three possible
        # domains and let the user's robot_name argument select the right one
        # at runtime.  Instead, we rely on setup_env.sh / the shell environment
        # and only ensure CYCLONEDDS_URI and RMW are correct here.
        SetEnvironmentVariable('RMW_IMPLEMENTATION', 'rmw_cyclonedds_cpp'),
        SetEnvironmentVariable('CYCLONEDDS_URI', f'file://{dds_cfg}'),
        # Private-domain nodes communicate only on localhost (keeps scan/TF/IMU
        # traffic off-network).  domain_bridge overrides this for its own
        # participants by using SUBNET discovery (set in odom_bridge.launch.py).
        SetEnvironmentVariable('ROS_AUTOMATIC_DISCOVERY_RANGE', 'LOCALHOST'),

        SetEnvironmentVariable('MACHINE_TYPE', 'MentorPi_Mecanum'),
        SetEnvironmentVariable('LIDAR_TYPE', 'LD19'),

        DeclareLaunchArgument(
            'map', default_value='map_01',
            description='Map name without extension in navigation/config/maps.'),
        DeclareLaunchArgument(
            'robot_name', default_value='robot1',
            description='Robot namespace: robot1, robot2, or robot3.'),
        DeclareLaunchArgument(
            'use_sim_time', default_value='false',
            description='Use simulation clock if true.'),
        DeclareLaunchArgument(
            'launch_costmap', default_value='false',
            description='Launch Nav2 global costmap.'),

        OpaqueFunction(function=launch_setup),
    ])
