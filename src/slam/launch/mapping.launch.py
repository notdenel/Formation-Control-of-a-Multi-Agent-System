"""
Combined bringup for SLAM mapping (replaces four separate launch commands).

  ros2 launch slam mapping.launch.py

Teleop (run separately from WSL while mapping):
  ros2 run peripherals teleop_key_control
  # or, if xterm/WSLg is available:
  ros2 launch peripherals teleop_key_control.launch.py

Save the finished map:
  ros2 service call /map_save_node/save_map std_srvs/srv/Trigger

Map is written to ~/ros2_ws/src/slam/maps/map_01.pgm + map_01.yaml

Startup order
-------------
  t=0s   controller   – wheel odometry, EKF, IMU filter  (odom TF source)
  t=0s   lidar        – scan_raw topic
  t=0s   rf2o         – laser odometry (odom_rf2o topic)
  t=10s  slam_toolbox – waits for TF tree to stabilise before first scan
  t=10s  map_save     – service node for saving the map
"""
import os
from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription, LaunchService
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.actions import IncludeLaunchDescription, OpaqueFunction, TimerAction


def launch_setup(context):
    compiled = os.environ.get('need_compile', 'False')

    # Python packages — support both source-tree and install-tree modes.
    if compiled == 'True':
        slam_pkg        = get_package_share_directory('slam')
        controller_pkg  = get_package_share_directory('controller')
        peripherals_pkg = get_package_share_directory('peripherals')
    else:
        slam_pkg        = '/home/agent3/ros2_ws/src/slam'
        controller_pkg  = '/home/agent3/ros2_ws/src/driver/controller'
        peripherals_pkg = '/home/agent3/ros2_ws/src/peripherals'

    # C++ package — always use the installed share directory.
    rf2o_pkg = get_package_share_directory('rf2o_laser_odometry')

    controller_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(controller_pkg, 'launch/controller.launch.py')),
    )

    lidar_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(peripherals_pkg, 'launch/lidar.launch.py')),
    )

    rf2o_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(rf2o_pkg, 'launch/rf2o_laser_odometry.launch.py')),
    )

    # slam_toolbox + map_save node — delayed so the TF tree (odom → base_footprint)
    # is already published by the EKF before the first lidar scan is processed.
    slam_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(slam_pkg, 'launch/include/slam_base.launch.py')),
        launch_arguments={'enable_save': 'true'}.items(),
    )

    return [
        controller_launch,
        lidar_launch,
        rf2o_launch,
        TimerAction(period=10.0, actions=[slam_launch]),
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
