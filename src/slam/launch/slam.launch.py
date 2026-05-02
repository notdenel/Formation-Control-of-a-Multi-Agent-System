from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource

from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():

    # Controller
    controller_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory('controller'),
                'launch',
                'controller.launch.py'
            )
        )
    )

    # Lidar
    lidar_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory('peripherals'),
                'launch',
                'lidar.launch.py'
            )
        )
    )

    # RF2O Odometry
    rf2o_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory('rf2o_laser_odometry'),
                'launch',
                'rf2o_laser_odometry.launch.py'
            )
        )
    )

    # SLAM
    slam_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory('slam'),
                'launch',
                'slam_mapping.launch.py'
            )
        )
    )

    return LaunchDescription([
        controller_launch,
        lidar_launch,
        rf2o_launch,
        slam_launch
    ])