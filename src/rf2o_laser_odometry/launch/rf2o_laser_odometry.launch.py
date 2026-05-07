from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    scan_raw = LaunchConfiguration('scan_raw')
    odom_topic = LaunchConfiguration('odom_topic')
    base_frame_id = LaunchConfiguration('base_frame_id')
    odom_frame_id = LaunchConfiguration('odom_frame_id')
    publish_tf = LaunchConfiguration('publish_tf')
    freq = LaunchConfiguration('freq')

    return LaunchDescription([
        DeclareLaunchArgument(
            'scan_raw',
            default_value='scan_raw',
            description='Laser scan topic. Use a relative topic so namespaces resolve correctly.'
        ),

        DeclareLaunchArgument(
            'odom_topic',
            default_value='odom_rf2o',
            description='RF2O odometry output topic. Use a relative topic so namespaces resolve correctly.'
        ),

        DeclareLaunchArgument(
            'base_frame_id',
            default_value='base_footprint',
            description='Base frame used by RF2O.'
        ),

        DeclareLaunchArgument(
            'odom_frame_id',
            default_value='odom',
            description='Odometry frame used by RF2O.'
        ),

        DeclareLaunchArgument(
            'publish_tf',
            default_value='false',
            description='Whether RF2O should publish odom -> base TF.'
        ),

        DeclareLaunchArgument(
            'freq',
            default_value='10.0',
            description='RF2O update frequency.'
        ),

        Node(
            package='rf2o_laser_odometry',
            executable='rf2o_laser_odometry_node',
            name='rf2o_laser_odometry',
            output='screen',
            parameters=[{
                'laser_scan_topic': scan_raw,
                'odom_topic': odom_topic,
                'publish_tf': publish_tf,
                'base_frame_id': base_frame_id,
                'odom_frame_id': odom_frame_id,
                'init_pose_from_topic': '',
                'freq': freq,
            }],
        ),
    ])