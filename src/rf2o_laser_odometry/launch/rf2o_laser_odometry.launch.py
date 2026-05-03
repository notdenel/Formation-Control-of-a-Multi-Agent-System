import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy

def generate_launch_description() -> LaunchDescription:

    scan_raw_arg = DeclareLaunchArgument(
        'scan_raw', default_value='scan_raw',
        description='Topic name for raw lidar scan data (must match lidar.launch.py)',
    )
    odom_topic_arg = DeclareLaunchArgument(
        'odom_topic', default_value='odom_rf2o',
        description='Topic name for odometry output',
    )
    base_frame_arg = DeclareLaunchArgument(
        'base_frame_id', default_value='base_footprint',
        description='Base frame ID',
    )
    odom_frame_arg = DeclareLaunchArgument(
        'odom_frame_id', default_value='odom',
        description='Odometry frame ID',
    )

    rf2o_node = Node(
        package='rf2o_laser_odometry',
        executable='rf2o_laser_odometry_node',
        output='screen',
        parameters=[{
            'laser_scan_topic':     LaunchConfiguration('scan_raw'),
            'odom_topic':           LaunchConfiguration('odom_topic'),
            'publish_tf':           False,
            'base_frame_id':        LaunchConfiguration('base_frame_id'),
            'odom_frame_id':        LaunchConfiguration('odom_frame_id'),
            'init_pose_from_topic': '',
            'freq':                 10.0,
            'laser_scan_topic_qos': 'reliable',   # ← match the LD19 publisher
        }],
    )

    return LaunchDescription([
        scan_raw_arg,
        odom_topic_arg,
        base_frame_arg,
        odom_frame_arg,
        rf2o_node,
    ])