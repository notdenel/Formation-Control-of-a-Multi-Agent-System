"""
DOES NOT WORK
"""
import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription, LaunchService
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
    compiled = os.environ.get('need_compile', 'False')

    sim = LaunchConfiguration('sim', default='false').perform(context)
    robot_name = LaunchConfiguration('robot_name', default='').perform(context)
    master_name = LaunchConfiguration('master_name', default='').perform(context)

    frame_prefix = '' if robot_name in ['', '/'] else f'{robot_name}/'
    use_sim_time = 'true' if sim == 'true' else 'false'

    map_frame  = f'{frame_prefix}map'
    odom_frame = f'{frame_prefix}odom'
    base_frame = f'{frame_prefix}base_footprint'
    scan_topic = f'{frame_prefix}scan_raw'

    compiled = os.environ.get('need_compile', 'False').strip().lower() == 'true'
    
    slam_package_path = get_package_share_directory('slam')

    # -----------------------
    # Robot drivers (controller + lidar)
    # -----------------------
    robot_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(slam_package_path, 'launch/include/robot.launch.py')
        ),
        launch_arguments={
            'sim': sim,
            'master_name': master_name,
            'robot_name': robot_name,
            'use_joy': 'false',
        }.items(),
    )

    # -----------------------
    # SLAM Toolbox (delayed to let drivers come up first)
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
        PushRosNamespace(robot_name) if robot_name not in ['', '/'] else GroupAction([]),
        robot_launch,
        TimerAction(period=10.0, actions=[slam_launch]),
    ])

    return [
        DeclareLaunchArgument('sim', default_value='false'),
        DeclareLaunchArgument('robot_name', default_value=''),
        DeclareLaunchArgument('master_name', default_value=''),
        bringup,
    ]


def generate_launch_description():
    return LaunchDescription([
        OpaqueFunction(function=launch_setup)
    ])


if __name__ == '__main__':
    ld = generate_launch_description()
    ls = LaunchService()
    ls.include_launch_description(ld)
    ls.run()