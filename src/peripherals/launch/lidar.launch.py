import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


# Maps lidar type -> (launch file, filter config)
# Add new lidar types here rather than chaining if/elif blocks.
_LIDAR_CONFIGS: dict[str, tuple[str, str]] = {
    'A1':     ('ldlidar_LD19.launch.py',  'lidar_filters_config_a1.yaml'),
    'G4':     ('ldlidar_LD19.launch.py',  'lidar_filters_config_g4.yaml'),
    'LD06':   ('ldlidar_LD06.launch.py',  'lidar_filters_config_ld19.yaml'),
    'LD06P':  ('ldlidar_LD06.launch.py',  'lidar_filters_config_ld19.yaml'),
    'STL27L': ('ldlidar_LD06.launch.py',  'lidar_filters_config_ld19.yaml'),
    'LD14P':  ('ldlidar_LD19.launch.py',  'lidar_filters_config_ld14p.yaml'),
    'LD19':   ('ldlidar_LD19.launch.py',  'lidar_filters_config_ld19.yaml'),
    'MS200':  ('ms200_scan.launch.py',    'lidar_filters_config_ms200.yaml'),
}
_DEFAULT_LIDAR = 'LD19'


def generate_launch_description() -> LaunchDescription:
    lidar_type = os.environ.get('LIDAR_TYPE', _DEFAULT_LIDAR)

    if lidar_type not in _LIDAR_CONFIGS:
        import warnings
        warnings.warn(
            f"Unknown LIDAR_TYPE '{lidar_type}', falling back to '{_DEFAULT_LIDAR}'.",
            stacklevel=2,
        )
        lidar_type = _DEFAULT_LIDAR

    launch_file, filter_config = _LIDAR_CONFIGS[lidar_type]

    pkg = get_package_share_directory('peripherals')
    lidar_launch_path      = os.path.join(pkg, 'launch', 'include', launch_file)
    laser_filters_config   = os.path.join(pkg, 'config', filter_config)

    # Declare arguments
    lidar_frame_arg = DeclareLaunchArgument(
        'lidar_frame', default_value='lidar_frame',
        description='TF frame ID for the lidar',
    )
    scan_raw_arg = DeclareLaunchArgument(
        'scan_raw', default_value='scan_raw',
        description='Topic name for raw lidar scan data',
    )
    scan_topic_arg = DeclareLaunchArgument(
        'scan_topic', default_value='scan',
        description='Topic name for filtered lidar scan data',
    )

    lidar_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(lidar_launch_path),
        launch_arguments={
            'scan_raw':    LaunchConfiguration('scan_raw'),
            'lidar_frame': LaunchConfiguration('lidar_frame'),
        }.items(),
    )

    laser_filter_node = Node(
        package='laser_filters',
        executable='scan_to_scan_filter_chain',
        output='screen',
        parameters=[laser_filters_config],
        remappings=[
            ('scan',          LaunchConfiguration('scan_raw')),
            ('scan_filtered', LaunchConfiguration('scan_topic')),
        ],
    )

    return LaunchDescription([
        lidar_frame_arg,
        scan_raw_arg,
        scan_topic_arg,
        lidar_launch,
        # Uncomment to re-enable laser filtering:
        # laser_filter_node,
    ])


if __name__ == '__main__':
    from launch.launch_service import LaunchService  # fixed missing import
    ld = generate_launch_description()
    ls = LaunchService()
    ls.include_launch_description(ld)
    ls.run()