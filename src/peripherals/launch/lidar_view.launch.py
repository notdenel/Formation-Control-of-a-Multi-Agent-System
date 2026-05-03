import os
from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():

    robot_name = LaunchConfiguration('robot_name')

    compiled = os.environ.get('need_compile', 'True').lower() == 'true'

    if compiled:
        mentorpi_description_package_path = get_package_share_directory('mentorpi_description')
        peripherals_package_path = get_package_share_directory('peripherals')
    else:
        mentorpi_description_package_path = '/home/ubuntu/ros2_ws/src/simulations/mentorpi_description'
        peripherals_package_path = '/home/ubuntu/ros2_ws/src/peripherals'

    # ---------------- ROBOT DESCRIPTION ----------------
    robot_description_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(mentorpi_description_package_path, 'launch', 'robot_description.launch.py')
        ),
        launch_arguments={
            'frame_prefix': robot_name,
            'use_gui': 'false',
            'use_rviz': 'false',
            'use_sim_time': 'false',
            'use_namespace': 'true',
            'namespace': robot_name,
        }.items()
    )

    # ---------------- LIDAR ----------------
    lidar_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(peripherals_package_path, 'launch', 'lidar.launch.py')
        ),
        launch_arguments={
            'namespace': robot_name,
        }.items()
    )

    # ---------------- RVIZ (GLOBAL PREFERRED) ----------------
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        arguments=['-d', os.path.join(peripherals_package_path, 'rviz', 'lidar_view.rviz')],
        output='screen',
    )

    return LaunchDescription([
        DeclareLaunchArgument('robot_name', default_value='robot1'),

        robot_description_launch,
        lidar_launch,
        rviz_node,
    ])