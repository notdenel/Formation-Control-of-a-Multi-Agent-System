import os
from ament_index_python.packages import get_package_share_directory

from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument, OpaqueFunction, TimerAction
from launch import LaunchDescription
from launch.substitutions import LaunchConfiguration


def launch_setup(context):
    enable_save  = LaunchConfiguration('enable_save').perform(context)
    use_sim_time = LaunchConfiguration('use_sim_time').perform(context)
    map_frame    = LaunchConfiguration('map_frame').perform(context)
    odom_frame   = LaunchConfiguration('odom_frame').perform(context)
    base_frame   = LaunchConfiguration('base_frame').perform(context)
    scan_topic   = LaunchConfiguration('scan_topic').perform(context)
    namespace    = LaunchConfiguration('namespace').perform(context)

    use_sim_time_bool = use_sim_time.lower() == 'true'

    slam_package_path = get_package_share_directory('slam')

    # slam_toolbox's map publishers (/map, /map_metadata) are created with
    # absolute paths inside karto_mapper and ignore PushRosNamespace.
    # Explicit absolute->absolute remaps move them under our namespace so
    # they don't leak to root and conflict with other robots on the network.
    # The scan subscription is handled via the 'scan_topic' parameter below
    # (NOT via a 'scan' remap — slam_toolbox honors the parameter directly
    # and resolves it relative to its own namespace).
    map_remaps = []
    if namespace:
        map_remaps = [
            ('/map',          f'/{namespace}/map'),
            ('/map_metadata', f'/{namespace}/map_metadata'),
        ]

    sync_node = Node(
        package='slam_toolbox',
        executable='sync_slam_toolbox_node',
        name='slam_toolbox',
        output='screen',
        parameters=[
            os.path.join(slam_package_path, 'config/slam.yaml'),
            {
                'use_sim_time': use_sim_time_bool,
                'map_frame':    map_frame,    # global, e.g. 'map'
                'odom_frame':   odom_frame,   # qualified, e.g. 'robot1/odom'
                'base_frame':   base_frame,   # qualified, e.g. 'robot1/base_footprint'
                'scan_topic':   scan_topic,   # relative, e.g. 'scan_raw'
                'enable_interactive_mode': True,
            },
        ],
        remappings=map_remaps,
    )

    # Lifecycle manager configures + activates slam_toolbox automatically.
    # bond_timeout 0.0 disables the heartbeat check (slam_toolbox sends no bonds).
    # 5 s period gives slow Pi boots enough time to register before configure.
    lifecycle_manager = TimerAction(
        period=5.0,
        actions=[Node(
            package='nav2_lifecycle_manager',
            executable='lifecycle_manager',
            name='lifecycle_manager_slam',
            output='screen',
            parameters=[{
                'use_sim_time': use_sim_time_bool,
                'autostart':    True,
                'bond_timeout': 0.0,
                'node_names':   ['slam_toolbox'],
            }],
        )],
    )

    actions = [sync_node, lifecycle_manager]

    # map_save node: launched only when enable_save is true.
    # Provides ~/save_map (Trigger) — call it when the map is ready:
    #   ros2 service call /<ns>/map_save_node/save_map std_srvs/srv/Trigger
    if enable_save == 'true':
        actions.append(Node(
            package='slam',
            executable='map_save',
            name='map_save_node',
            output='screen',
        ))

    return actions


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('namespace',    default_value=''),
        DeclareLaunchArgument('enable_save',  default_value='true'),
        DeclareLaunchArgument('use_sim_time', default_value='false'),
        DeclareLaunchArgument('map_frame',    default_value='map'),
        DeclareLaunchArgument('odom_frame',   default_value='odom'),
        DeclareLaunchArgument('base_frame',   default_value='base_footprint'),
        DeclareLaunchArgument('scan_topic',   default_value='scan_raw'),
        OpaqueFunction(function=launch_setup),
    ])