import os
from ament_index_python.packages import get_package_share_directory

from launch_ros.actions import Node
from nav2_common.launch import RewrittenYaml
from launch.actions import DeclareLaunchArgument, OpaqueFunction, TimerAction
from launch import LaunchDescription, LaunchService
from launch.substitutions import LaunchConfiguration


def launch_setup(context):
    compiled = os.environ.get('need_compile', 'False')

    enable_save  = LaunchConfiguration('enable_save',  default='true').perform(context)
    use_sim_time = LaunchConfiguration('use_sim_time', default='false')
    map_frame    = LaunchConfiguration('map_frame',    default='map')
    odom_frame   = LaunchConfiguration('odom_frame',   default='odom')
    base_frame   = LaunchConfiguration('base_frame',   default='base_footprint')
    scan_topic   = LaunchConfiguration('scan_topic',   default='scan_raw')

    enable_save_arg  = DeclareLaunchArgument('enable_save',  default_value=enable_save)
    use_sim_time_arg = DeclareLaunchArgument('use_sim_time', default_value=use_sim_time)
    map_frame_arg    = DeclareLaunchArgument('map_frame',    default_value=map_frame)
    odom_frame_arg   = DeclareLaunchArgument('odom_frame',   default_value=odom_frame)
    base_frame_arg   = DeclareLaunchArgument('base_frame',   default_value=base_frame)
    scan_topic_arg   = DeclareLaunchArgument('scan_topic',   default_value=scan_topic)

    slam_package_path = get_package_share_directory('slam')

    slam_params = RewrittenYaml(
        source_file=os.path.join(slam_package_path, 'config/slam.yaml'),
        param_rewrites={
            'use_sim_time': use_sim_time,
            'map_frame':    map_frame,
            'odom_frame':   odom_frame,
            'base_frame':   base_frame,
            'scan_topic':   scan_topic,
        },
        convert_types=True
    )

    remappings = [
        ('/tf',           'tf'),
        ('/tf_static',    'tf_static'),
        ('/map',          'map'),
        ('/map_metadata', 'map_metadata'),
        ('scan', 'scan_raw'),
    ]

    sync_node = Node(
        package='slam_toolbox',
        executable='sync_slam_toolbox_node',
        name='slam_toolbox',
        output='screen',
        parameters=[slam_params],
        remappings=remappings,
    )

    # NOTE: robot_state_publisher is intentionally NOT launched here.
    # It is already started by controller.launch.py (bringup).  Launching a
    # second instance here causes two nodes to publish /tf_static for the same
    # frames (base_footprint → lidar_frame), producing conflicting transforms
    # that slam_toolbox sees as the sensor jumping between poses on every scan —
    # the direct cause of the multiple-ghost-outline artifact in the map image.
    # If you ever run slam_base.launch.py standalone (without bringup), you must
    # start robot_state_publisher separately before launching this file.

    # Lifecycle manager configures and activates slam_toolbox automatically.
    # bond_timeout 0.0 disables the heartbeat check (slam_toolbox sends no bonds).
    # Period raised from 2 s → 5 s: on a Pi under load at startup the node may
    # not finish registering within 2 s, causing a silent configure-abort that
    # leaves slam_toolbox accepting scans in an uninitialised state.
    lifecycle_manager = TimerAction(
        period=5.0,
        actions=[Node(
            package='nav2_lifecycle_manager',
            executable='lifecycle_manager',
            name='lifecycle_manager_slam',
            output='screen',
            parameters=[{
                'use_sim_time': use_sim_time,
                'autostart':    True,
                'bond_timeout': 0.0,
                'node_names':   ['slam_toolbox'],
            }],
        )],
    )

    actions = [
        enable_save_arg,
        use_sim_time_arg,
        map_frame_arg,
        odom_frame_arg,
        base_frame_arg,
        scan_topic_arg,
        sync_node,
        lifecycle_manager,
    ]

    # map_save node: launched only when enable_save is true.
    # Provides ~/save_map (Trigger) — call it when the map is ready:
    #   ros2 service call /map_save_node/save_map std_srvs/srv/Trigger
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
        OpaqueFunction(function=launch_setup)
    ])


if __name__ == '__main__':
    ld = generate_launch_description()
    ls = LaunchService()
    ls.include_launch_description(ld)
    ls.run()