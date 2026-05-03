import os
from ament_index_python.packages import get_package_share_directory
from launch_ros.actions import Node
from launch import LaunchDescription, LaunchService
from launch.substitutions import LaunchConfiguration
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource

from launch_ros.actions import PushRosNamespace

def generate_launch_description():
    robot_name = LaunchConfiguration('robot_name')

    robot_controller_package_path = get_package_share_directory('ros_robot_controller')
    peripherals_package_path = get_package_share_directory('peripherals')

    robot_controller_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(robot_controller_package_path, 'launch/ros_robot_controller.launch.py')
        ),
        launch_arguments={
            'imu_frame': 'imu_frame',
        }.items()
    )

    tf_broadcaster_imu_node = Node(
        package='peripherals',
        executable='tf_broadcaster_imu',
        output='screen',
        parameters=[
            {'imu_topic': 'imu'},
            {'imu_frame': 'imu_frame'},
            {'imu_link': 'imu_link'}
        ]
    )

    imu_filter_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(peripherals_package_path, 'launch/imu_filter.launch.py')
        )
    )

    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        arguments=['-d', os.path.join(peripherals_package_path, 'rviz/imu_view.rviz')],
        output='screen',
    )

    return LaunchDescription([
        # Declare namespace
        DeclareLaunchArgument(
            'robot_name',
            default_value='robot1'
        ),
        # Apply namespace to everything below
        PushRosNamespace(robot_name),
        
        robot_controller_launch,
        tf_broadcaster_imu_node,
        imu_filter_launch,
        rviz_node,
    ])


if __name__ == '__main__':
    ld = generate_launch_description()

    ls = LaunchService()
    ls.include_launch_description(ld)
    ls.run()
