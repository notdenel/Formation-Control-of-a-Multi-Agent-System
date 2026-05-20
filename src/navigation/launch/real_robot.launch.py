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

For the final formation-control demo, launch_costmap is false by default because
the controller only needs each robot's pose and /robotX/controller/cmd_vel. Nav2
costmaps can be re-enabled later after their scan-topic configuration is verified.

Expected robot-local topics:

  /robotX/scan_raw
  /robotX/odom_raw
  /robotX/odom_rf2o
  /robotX/odom
  /robotX/imu
  /robotX/amcl_pose
  /robotX/position
  /robotX/controller/cmd_vel

Expected TF tree:

  map
  ├── robot1/odom -> robot1/base_footprint -> robot1/lidar_frame
  ├── robot2/odom -> robot2/base_footprint -> robot2/lidar_frame
  └── robot3/odom -> robot3/base_footprint -> robot3/lidar_frame

DDS setup:

  CycloneDDS static peers are configured through:
    src/navigation/config/cyclone_dds.xml

  This launch file sets:
    ROS_DOMAIN_ID=10
    RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
    CYCLONEDDS_URI=file://.../cyclone_dds.xml
    MACHINE_TYPE=MentorPi_Mecanum
    LIDAR_TYPE=LD19
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


# Single source of truth for robot-local topic names.
# These are intentionally relative so PushRosNamespace(robot_name) resolves them to:
#   /robot1/scan_raw, /robot2/scan_raw, /robot3/scan_raw
#   /robot1/odom_rf2o, /robot2/odom_rf2o, /robot3/odom_rf2o
_SCAN_TOPIC = 'scan_raw'
_RF2O_ODOM_TOPIC = 'odom_rf2o'


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
    costmap_params = os.path.join(pkg_nav, 'config', 'multi_robot_costmap.yaml')

    # Frame IDs must be explicitly namespaced.
    # PushRosNamespace affects topic names and node names, but not message frame_id fields.
    odom_frame = f'{robot_name}/odom'
    base_frame = f'{robot_name}/base_footprint'
    imu_frame = f'{robot_name}/imu_link'
    lidar_frame = f'{robot_name}/lidar_frame'

    # EKF config uses "namespace/" as a placeholder.
    # Replace it with "robotX/" so frame IDs become robotX/odom, robotX/base_footprint, etc.
    ekf_param = ReplaceString(
        source_file=os.path.join(pkg_ctrl, 'config', 'ekf.yaml'),
        replacements={'namespace/': f'{robot_name}/'},
    )

    # Lidar driver.
    # Inside PushRosNamespace(robot_name), scan_raw resolves to /robotX/scan_raw.
    # base_frame must be passed as the fully-qualified name so lidar.launch.py's
    # qualify() leaves it unchanged and the static TF publishes
    # robot1/base_footprint → robot1/lidar_frame (not bare base_footprint).
    lidar = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(lidar_launch),
        launch_arguments={
            'scan_raw': _SCAN_TOPIC,
            'lidar_frame': lidar_frame,
            'base_frame': base_frame,
        }.items(),
    )

    # Hardware driver + wheel-encoder odometry.
    # use_namespace is false because this file already applies PushRosNamespace(robot_name).
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

    # IMU complementary filter.
    # The raw IMU topic from the controller is namespaced, so remap the absolute input.
    # The output "imu" is relative and becomes /robotX/imu.
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

    # RF2O laser odometry.
    # This assumes rf2o_laser_odometry.launch.py has been updated to declare:
    #   scan_raw
    #   odom_topic
    #   base_frame_id
    #   odom_frame_id
    #   publish_tf
    #   freq
    #
    # Topics are relative and are resolved by PushRosNamespace(robot_name).
    # Frame IDs are already fully qualified.
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

    # Static TF: base_footprint -> imu_link.
    imu_static_tf = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='imu_static_tf',
        output='screen',
        arguments=[
            '--x', '0.0',
            '--y', '0.0',
            '--z', '0.0',
            '--roll', '0.0',
            '--pitch', '0.0',
            '--yaw', '0.0',
            '--frame-id', base_frame,
            '--child-frame-id', imu_frame,
        ],
    )

    # EKF.
    # Publishes /robotX/odom and TF robotX/odom -> robotX/base_footprint.
    ekf = Node(
        package='robot_localization',
        executable='ekf_node',
        name='ekf_filter_node',
        output='screen',
        parameters=[ekf_param, {'use_sim_time': use_sim_time_bool}],
        remappings=[
            ('odometry/filtered', 'odom'),
        ],
    )

    # Pose normalizer.
    # Publishes /robotX/position, /robotX/tf_pose, and /robotX/odom_pose.
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

    # Robot-local hardware/perception/local odometry group.
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

    # AMCL + map server.
    # Kept outside bringup_group because single_robot.launch.py already handles its own namespace.
    localization = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(single_launch),
        launch_arguments={
            'robot_name': robot_name,
            'use_sim_time': use_sim_time,
            'map': map_name,
            'scan_topic': _SCAN_TOPIC,
        }.items(),
    )

    odom_bridge_launch = os.path.join(pkg_nav, 'launch', 'odom_bridge.launch.py')
    odom_bridge = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(odom_bridge_launch),
        launch_arguments={'robot_name': robot_name}.items(),
    )

    # Aggregation — runs locally on this robot in its private domain.
    # Delayed 20 s so the EKF is publishing odom and the domain_bridge has
    # connected to the fleet domain before discovery runs.
    # Peer /robotY/odom and /robotZ/odom arrive via odom_bridge (domain 10 →
    # private domain), so aggregation sees all robots without a cmd_vel bridge.
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

    # Optional costmap.
    # Disabled by default because the existing costmap YAML may still need topic cleanup.
    # Formation control does not need this to run.
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

        delayed_costmap = TimerAction(
            period=15.0,
            actions=[costmap_group],
        )

        actions.append(delayed_costmap)

    return actions


def generate_launch_description():
    return LaunchDescription([
        # ROS_DOMAIN_ID is inherited from the shell (setup_robot.sh) so that
        # each robot's local nodes run in its private domain (11/12/13).
        # RMW_IMPLEMENTATION and CYCLONEDDS_URI must be set here explicitly
        # because domain_bridge (launched by odom_bridge.launch.py) needs
        # the static-peer XML to find domain-10 participants on the LAN.
        # Multicast is disabled in cyclone_dds.xml, so without this URI the
        # bridge stays localhost-only and /robotX/odom never reaches the WSL.
        SetEnvironmentVariable('RMW_IMPLEMENTATION', 'rmw_cyclonedds_cpp'),
        SetEnvironmentVariable(
            'CYCLONEDDS_URI',
            os.path.join(
                get_package_share_directory('navigation'),
                'config', 'cyclone_dds.xml')),

        # Hardware platform settings.
        SetEnvironmentVariable('MACHINE_TYPE', 'MentorPi_Mecanum'),
        SetEnvironmentVariable('LIDAR_TYPE', 'LD19'),

        DeclareLaunchArgument(
            'map',
            default_value='map_01',
            description='Map name without extension, located in navigation/config/maps.',
        ),

        DeclareLaunchArgument(
            'robot_name',
            default_value='robot1',
            description='Robot namespace: robot1, robot2, or robot3.',
        ),

        DeclareLaunchArgument(
            'use_sim_time',
            default_value='false',
            description='Use simulation clock if true.',
        ),

        DeclareLaunchArgument(
            'launch_costmap',
            default_value='false',
            description='Launch Nav2 global costmap. Disabled by default for formation-control testing.',
        ),

        OpaqueFunction(function=launch_setup),
    ])