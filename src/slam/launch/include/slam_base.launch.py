import os
from ament_index_python.packages import get_package_share_directory

from launch_ros.actions import Node
from nav2_common.launch import RewrittenYaml
from launch.actions import DeclareLaunchArgument, OpaqueFunction, TimerAction
from launch import LaunchDescription, LaunchService
from launch.substitutions import Command, LaunchConfiguration
from pathlib import Path

def launch_setup(context):
    compiled = os.environ.get('need_compile', 'False')
    enable_save = LaunchConfiguration('enable_save', default='true').perform(context)
    use_sim_time = LaunchConfiguration('use_sim_time', default='false')
    map_frame = LaunchConfiguration('map_frame', default='map')
    odom_frame = LaunchConfiguration('odom_frame', default='odom')
    base_frame = LaunchConfiguration('base_frame', default='base_footprint')
    scan_topic = LaunchConfiguration('scan_topic', default='scan_raw')

    enable_save_arg = DeclareLaunchArgument('enable_save', default_value=enable_save)
    use_sim_time_arg = DeclareLaunchArgument('use_sim_time', default_value=use_sim_time)
    map_frame_arg = DeclareLaunchArgument('map_frame', default_value=map_frame)
    odom_frame_arg = DeclareLaunchArgument('odom_frame', default_value=odom_frame)
    base_frame_arg = DeclareLaunchArgument('base_frame', default_value=base_frame)
    scan_topic_arg = DeclareLaunchArgument('scan_topic', default_value=scan_topic)

    if compiled == 'True':
        slam_package_path = get_package_share_directory('slam')
    else:
        slam_package_path = str(Path.home() / 'ros2_ws/src/slam')

    slam_params = RewrittenYaml(
        source_file=os.path.join(slam_package_path, 'config/slam.yaml'),
        param_rewrites={
            'use_sim_time': use_sim_time,
            'map_frame': map_frame,
            'odom_frame': odom_frame,
            'base_frame': base_frame,
            'scan_topic': scan_topic,
        },
        convert_types=True
    )

    remappings = [
        ('/tf', 'tf'),
        ('/tf_static', 'tf_static'),
        ('/map', 'map'),
        ('/map_metadata', 'map_metadata'),
    ]

    sync_node = Node(
        package='slam_toolbox',
        executable='sync_slam_toolbox_node',
        name='slam_toolbox',
        output='screen',
        parameters=[slam_params],
        remappings=remappings
    )

    # robot_state_publisher broadcasts the static TF tree from the URDF
    # (base_footprint → base_link → lidar_frame).  Without it slam_toolbox
    # drops every scan with "frame 'lidar_frame' … discarding message".
    mentorpi_pkg = get_package_share_directory('mentorpi_description')
    urdf_path = os.path.join(mentorpi_pkg, 'urdf', 'mentorpi.xacro')
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[{
            'robot_description': Command(['xacro ', urdf_path]),
            'use_sim_time': use_sim_time,
        }],
        remappings=[('/tf', 'tf'), ('/tf_static', 'tf_static')],
    )

    # nav2_lifecycle_manager configures and activates slam_toolbox automatically.
    # bond_timeout 0.0 disables the heartbeat check — slam_toolbox does not send
    # lifecycle bonds, so the default 4 s timeout would abort bringup.
    # Delayed 2 s to give the node time to fully register before configure is called.
    lifecycle_manager = TimerAction(
        period=2.0,
        actions=[Node(
            package='nav2_lifecycle_manager',
            executable='lifecycle_manager',
            name='lifecycle_manager_slam',
            output='screen',
            parameters=[{
                'use_sim_time': use_sim_time,
                'autostart': True,
                'bond_timeout': 0.0,
                'node_names': ['slam_toolbox'],
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
        robot_state_publisher,
        sync_node,
        lifecycle_manager,
    ]

    # Launched only when enable_save is true.  Provides
    # ~/save_map (Trigger) — call it when the map is ready:
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
