"""
Start SLAM Toolbox for mapping, namespaced per robot.

Run each component in a separate terminal on the Pi:
  ros2 launch controller controller.launch.py             namespace:=robot1
  ros2 launch peripherals lidar.launch.py                 namespace:=robot1
  ros2 launch rf2o_laser_odometry rf2o_laser_odometry.launch.py namespace:=robot1
  ros2 launch slam slam_mapping.launch.py                 namespace:=robot1

Drive while mapping (separate terminal):
  ros2 run peripherals teleop_key_control --ros-args -r __ns:=/robot1

Save the map:
  ros2 service call /robot1/map_save_node/save_map std_srvs/srv/Trigger

Map is written to ~/ros2_ws/src/slam/maps/map_01.{pgm,yaml}.
"""
import os
from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.substitutions import LaunchConfiguration
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.actions import (
    DeclareLaunchArgument,
    GroupAction,
    IncludeLaunchDescription,
    OpaqueFunction,
)
from launch_ros.actions import PushRosNamespace


def launch_setup(context):
    namespace    = LaunchConfiguration('namespace').perform(context)
    use_sim_time = LaunchConfiguration('use_sim_time').perform(context)

    # Frame IDs must be fully qualified.
    prefix     = f'{namespace}/' if namespace else ''
    map_frame  = 'map'                       # global, NEVER namespaced
    odom_frame = f'{prefix}odom'
    base_frame = f'{prefix}base_footprint'

    slam_package_path = get_package_share_directory('slam')

    slam_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(slam_package_path, 'launch/include/slam_base.launch.py')),
        launch_arguments={
            'namespace':    namespace,        # NEW
            'use_sim_time': use_sim_time,
            'scan_topic':   'scan_raw',
            'odom_frame':   odom_frame,
            'base_frame':   base_frame,
            'map_frame':    map_frame,
            'enable_save':  'true',
        }.items(),
    )

    grouped = GroupAction([
        PushRosNamespace(namespace) if namespace else GroupAction([]),
        slam_launch,
    ])

    return [grouped]


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('namespace',    default_value=''),  # NEW
        DeclareLaunchArgument('enable_save',  default_value='true'),
        DeclareLaunchArgument('use_sim_time', default_value='false'),
        DeclareLaunchArgument('map_frame',    default_value='map'),
        DeclareLaunchArgument('odom_frame',   default_value='odom'),
        DeclareLaunchArgument('base_frame',   default_value='base_footprint'),
        DeclareLaunchArgument('scan_topic',   default_value='scan_raw'),
        OpaqueFunction(function=launch_setup),
    ])