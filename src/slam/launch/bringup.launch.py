import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    GroupAction,
    IncludeLaunchDescription,
    OpaqueFunction,
    TimerAction,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import PushRosNamespace


def launch_setup(context):

    sim = LaunchConfiguration('sim', default='false')
    robot_name = LaunchConfiguration('robot_name', default='')
    master_name = LaunchConfiguration('master_name', default='')

    sim_value = sim.perform(context)
    robot_name_value = robot_name.perform(context)
    master_name_value = master_name.perform(context)

    frame_prefix = '' if robot_name_value in ['', '/'] else f'{robot_name_value}/'

    use_sim_time = 'true' if sim_value == 'true' else 'false'

    map_frame  = f'{frame_prefix}map'
    odom_frame = f'{frame_prefix}odom'
    base_frame = f'{frame_prefix}base_footprint'
    scan_topic = f'{frame_prefix}scan_raw'

    slam_package_path = get_package_share_directory('slam')

    # -----------------------
    # Robot drivers (controller + lidar)
    # -----------------------
    robot_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(slam_package_path, 'launch/include/robot.launch.py')
        ),
        launch_arguments={
            'sim': sim_value,
            'master_name': master_name_value,
            'robot_name': robot_name_value,
            'use_joy': 'false',
        }.items(),
    )

    # -----------------------
    # SLAM Toolbox
    # -----------------------
    slam_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(slam_package_path, 'launch/include/slam_base.launch.py')
        ),
        launch_arguments={
            'use_sim_time': use_sim_time,
            'map_frame': map_frame,
            'odom_frame': odom_frame,
            'base_frame': base_frame,
            'scan_topic': scan_topic,
            'enable_save': 'true',
        }.items(),
    )

    bringup = GroupAction([
        PushRosNamespace(robot_name_value) if robot_name_value not in ['', '/'] else GroupAction([]),
        robot_launch,
        TimerAction(period=10.0, actions=[slam_launch]),
    ])

    return [
        DeclareLaunchArgument('sim', default_value='false'),
        DeclareLaunchArgument('robot_name', default_value=''),
        DeclareLaunchArgument('master_name', default_value=''),
        bringup
    ]


def generate_launch_description():
    return LaunchDescription([
        OpaqueFunction(function=launch_setup)
    ])