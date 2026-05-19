import os
from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription


def generate_launch_description():
    odom_frame = LaunchConfiguration('odom_frame')
    base_frame = LaunchConfiguration('base_frame')
    imu_frame  = LaunchConfiguration('imu_frame')

    robot_controller_package_path = get_package_share_directory('ros_robot_controller')
    controller_package_path       = get_package_share_directory('controller')

    # ros_robot_controller publishes /ros_robot_controller/imu_raw and subscribes
    # to /ros_robot_controller/set_motor etc. All relative. PushRosNamespace
    # applied by the parent launch (controller.launch.py) prefixes them.
    robot_controller_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(robot_controller_package_path, 'launch/ros_robot_controller.launch.py')
        ),
        launch_arguments={
            'imu_frame': imu_frame,  # already namespace-qualified by caller
        }.items()
    )

    odom_publisher_node = Node(
        package='controller',
        executable='odom_publisher',
        name='odom_publisher',
        output='screen',
        parameters=[
            os.path.join(controller_package_path, 'config/calibrate_params.yaml'),
            {
                'base_frame_id':  base_frame,   # already namespace-qualified
                'odom_frame_id':  odom_frame,   # already namespace-qualified
                'pub_odom_topic': True,
            }
        ],
        # No explicit remappings: all topics in odom_publisher_node are
        # relative ('odom_raw', 'controller/cmd_vel', 'set_pose', etc.) and
        # are namespaced automatically by the parent's PushRosNamespace.
    )

    return LaunchDescription([
        DeclareLaunchArgument('odom_frame', default_value='odom'),
        DeclareLaunchArgument('base_frame', default_value='base_footprint'),
        DeclareLaunchArgument('imu_frame',  default_value='imu_link'),
        robot_controller_launch,
        odom_publisher_node,
    ])