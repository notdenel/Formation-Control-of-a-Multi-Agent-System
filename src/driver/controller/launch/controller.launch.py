import os
from ament_index_python.packages import get_package_share_directory

from launch_ros.actions import Node, PushRosNamespace
from launch.conditions import IfCondition
from nav2_common.launch import ReplaceString
from launch import LaunchDescription
from launch.substitutions import LaunchConfiguration
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.actions import (
    DeclareLaunchArgument,
    GroupAction,
    IncludeLaunchDescription,
    OpaqueFunction,
)


def launch_setup(context):
    namespace    = LaunchConfiguration('namespace').perform(context)
    use_sim_time = LaunchConfiguration('use_sim_time').perform(context)
    enable_odom  = LaunchConfiguration('enable_odom')
    ekf_config   = LaunchConfiguration('ekf_config').perform(context)

    # Frame IDs must be fully qualified. PushRosNamespace does NOT rewrite
    # message header frame_id values.
    odom_frame_raw = LaunchConfiguration('odom_frame').perform(context)
    base_frame_raw = LaunchConfiguration('base_frame').perform(context)
    imu_frame_raw  = LaunchConfiguration('imu_frame').perform(context)

    def qualify(frame):
        if namespace and '/' not in frame:
            return f'{namespace}/{frame}'
        return frame

    odom_frame = qualify(odom_frame_raw)
    base_frame = qualify(base_frame_raw)
    imu_frame  = qualify(imu_frame_raw)

    peripherals_package_path = get_package_share_directory('peripherals')
    controller_package_path  = get_package_share_directory('controller')

    # Hardware driver + wheel-encoder odometry.
    # All topics inside this include are relative -> PushRosNamespace prefixes them.
    odom_publisher_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(controller_package_path, 'launch/odom_publisher.launch.py')
        ),
        launch_arguments={
            'imu_frame':  imu_frame,
            'base_frame': base_frame,
            'odom_frame': odom_frame,
        }.items()
    )

    # IMU filter is also defined in peripherals/launch/imu_filter.launch.py
    # but that file uses an ABSOLUTE remap (/ros_robot_controller/imu_raw) that
    # breaks under namespacing. Define the IMU filter inline here with the
    # correct namespaced remap, mirroring what real_robot.launch.py does.
    imu_filter_node = Node(
        package='imu_complementary_filter',
        executable='complementary_filter_node',
        name='imu_filter',
        output='screen',
        parameters=[{
            'use_mag': False,
            'do_bias_estimation': True,
            'do_adaptive_gain': True,
            'publish_debug_topics': False,
            'use_sim_time': use_sim_time.lower() == 'true',
        }],
        remappings=[
            # Absolute -> absolute: must include the namespace explicitly.
            ('imu/data_raw', f'/{namespace}/ros_robot_controller/imu_raw' if namespace
                              else '/ros_robot_controller/imu_raw'),
            ('imu/data',     'imu'),  # relative -> /robotX/imu
        ],
    )

    # Static TF: base_footprint -> imu_link.
    # Must use already-qualified frame IDs.
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

    # EKF.
    # ekf.yaml uses 'namespace/' as a placeholder. Replace with the actual
    # namespace prefix (or empty string).
    prefix = f'{namespace}/' if namespace else ''
    ekf_param = ReplaceString(
        source_file=os.path.join(controller_package_path, 'config', ekf_config),
        replacements={'namespace/': prefix},
    )

    ekf_filter_node = Node(
        package='robot_localization',
        executable='ekf_node',
        name='ekf_filter_node',
        output='screen',
        parameters=[ekf_param, {'use_sim_time': use_sim_time.lower() == 'true'}],
        remappings=[
            ('odometry/filtered', 'odom'),
            # Note: do NOT remap /tf or /tf_static here. PushRosNamespace
            # does not affect those topics (they are special-cased in ROS 2);
            # robot_localization writes to the global /tf as expected.
        ],
        condition=IfCondition(enable_odom),
    )

    grouped = GroupAction([
        PushRosNamespace(namespace) if namespace else GroupAction([]),
        odom_publisher_launch,
        imu_filter_node,
        imu_static_tf,
        ekf_filter_node,
    ])

    return [grouped]


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('namespace',    default_value=''),
        DeclareLaunchArgument('use_sim_time', default_value='false'),
        DeclareLaunchArgument('enable_odom',  default_value='true'),
        DeclareLaunchArgument('ekf_config',   default_value='ekf.yaml'),
        DeclareLaunchArgument('odom_frame',   default_value='odom'),
        DeclareLaunchArgument('base_frame',   default_value='base_footprint'),
        DeclareLaunchArgument('imu_frame',    default_value='imu_link'),
        OpaqueFunction(function=launch_setup),
    ])