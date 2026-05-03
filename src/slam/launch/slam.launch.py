from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os

# Single source of truth for the odometry topic name.
# Both RF2O (publisher) and SLAM toolbox (subscriber) read from this constant
# so a rename never causes a silent mismatch.
_ODOM_TOPIC = 'odom_rf2o'
_SCAN_TOPIC = 'scan_raw'


def generate_launch_description():

    # ── Controller ────────────────────────────────────────────────────────────
    controller_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory('controller'),
                'launch',
                'controller.launch.py',
            )
        )
    )

    # ── LiDAR (publishes /{_SCAN_TOPIC}) ──────────────────────────────────────
    lidar_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory('peripherals'),
                'launch',
                'lidar.launch.py',
            )
        ),
        # Explicitly forward the scan topic name so lidar.launch.py uses the
        # same string we pass to RF2O below.
        launch_arguments={
            'scan_raw': _SCAN_TOPIC,
        }.items(),
    )

    # ── RF2O laser odometry ───────────────────────────────────────────────────
    # Use IncludeLaunchDescription instead of a bare Node() so that
    # rf2o_laser_odometry.launch.py's declared arguments (QoS, frames, freq)
    # are all honoured.  We only override the two topic names.
    rf2o_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory('rf2o_laser_odometry'),
                'launch',
                'rf2o_laser_odometry.launch.py',
            )
        ),
        launch_arguments={
            # Must match what lidar.launch.py actually publishes.
            'scan_raw':   _SCAN_TOPIC,
            # RF2O publishes here; SLAM toolbox subscribes to the same string.
            'odom_topic': _ODOM_TOPIC,
        }.items(),
    )

    # ── SLAM toolbox ──────────────────────────────────────────────────────────
    # Forward the odometry topic so slam_mapping.launch.py passes it to the
    # slam_toolbox node's odom_topic parameter (or remapping).
    slam_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory('slam'),
                'launch',
                'slam_mapping.launch.py',
            )
        ),
        launch_arguments={
            'odom_topic': _ODOM_TOPIC,
            'scan_topic': _SCAN_TOPIC,
        }.items(),
    )

    # ── Map saver server ──────────────────────────────────────────────────────
    map_saver_server = Node(
        package='nav2_map_server',
        executable='map_saver_server',
        name='map_saver_server',
        output='screen',
        parameters=[{
            'save_map_timeout':        5.0,
            'free_thresh_default':     0.25,
            'occupied_thresh_default': 0.65,
        }],
    )

    return LaunchDescription([
        controller_launch,
        lidar_launch,
        rf2o_launch,
        slam_launch,
        map_saver_server,
    ])