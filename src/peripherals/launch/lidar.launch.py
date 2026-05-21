import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node, PushRosNamespace
from launch.actions import (
    DeclareLaunchArgument,
    GroupAction,
    IncludeLaunchDescription,
    OpaqueFunction,
)
from launch.substitutions import LaunchConfiguration
from launch.launch_description_sources import PythonLaunchDescriptionSource


def launch_setup(context, *args, **kwargs):
    lidar_type = os.environ.get('LIDAR_TYPE', 'LD19')

    namespace      = LaunchConfiguration('namespace').perform(context)
    base_frame_in  = LaunchConfiguration('base_frame').perform(context)
    lidar_frame_in = LaunchConfiguration('lidar_frame').perform(context)
    scan_raw_topic = LaunchConfiguration('scan_raw').perform(context)

    # Frame IDs are NOT auto-namespaced by ROS; we must qualify them ourselves.
    # If caller already passed a fully-qualified frame ('robot1/lidar_frame'),
    # keep it; otherwise prefix the namespace.
    def qualify(frame):
        if namespace and '/' not in frame:
            return f'{namespace}/{frame}'
        return frame

    base_frame  = qualify(base_frame_in)
    lidar_frame = qualify(lidar_frame_in)

    peripherals_package_path = get_package_share_directory('peripherals')
    if lidar_type == 'MS200':
        lidar_launch_path = os.path.join(peripherals_package_path, 'launch/include/ms200_scan.launch.py')
    elif lidar_type in ('LD06', 'LD06P', 'STL27L'):
        lidar_launch_path = os.path.join(peripherals_package_path, 'launch/include/ldlidar_LD06.launch.py')
    else:  # LD19 and default
        lidar_launch_path = os.path.join(peripherals_package_path, 'launch/include/ldlidar_LD19.launch.py')

    # The included lidar launch declares scan_raw + lidar_frame; we pass the
    # already-qualified lidar frame so messages publish with frame_id=robot1/lidar_frame.
    lidar_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(lidar_launch_path),
        launch_arguments={
            'scan_raw':    scan_raw_topic,
            'lidar_frame': lidar_frame,
        }.items()
    )

    # Static TF: base_footprint -> lidar_frame.
    # This MUST be published somewhere; slam_toolbox / AMCL / costmaps all need
    # to transform incoming scans into the base frame. Previously this lived
    # (broken) in odom_publisher.launch.py and (correctly but only when
    # localizing) in single_robot.launch.py. Putting it here makes it
    # available in both the mapping flow and the operations flow.
    lidar_static_tf = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='lidar_static_tf',
        output='screen',
        arguments=[
            '--x', '0.0', '--y', '0.0', '--z', '0.10',
            '--roll', '0.0', '--pitch', '0.0', '--yaw', '0.0',
            '--frame-id', base_frame,
            '--child-frame-id', lidar_frame,
        ],
    )

    # Everything that needs a namespace goes inside this group.
    # The static TF does not need PushRosNamespace (it doesn't publish on any
    # relative topic; only /tf and /tf_static which are remapped explicitly
    # by ROS 2's tf2_ros static_transform_publisher), but putting it in the
    # group keeps lifetime tied to the launch.
    grouped = GroupAction([
        PushRosNamespace(namespace) if namespace else GroupAction([]),
        lidar_launch,
        lidar_static_tf,
    ])

    return [grouped]


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument(
            'namespace', default_value='',
            description='Robot namespace (e.g. robot1). Empty = no namespace.'),
        DeclareLaunchArgument(
            'base_frame', default_value='base_footprint',
            description='Base TF frame; will be auto-qualified with namespace.'),
        DeclareLaunchArgument(
            'lidar_frame', default_value='lidar_frame',
            description='Lidar TF frame; will be auto-qualified with namespace.'),
        DeclareLaunchArgument(
            'scan_raw', default_value='scan_raw',
            description='Relative lidar topic name; PushRosNamespace prefixes it.'),
        OpaqueFunction(function=launch_setup),
    ])