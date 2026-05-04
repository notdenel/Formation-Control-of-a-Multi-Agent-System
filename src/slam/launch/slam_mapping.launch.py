"""
Start SLAM Toolbox for mapping (no robot bringup — run bringup components separately).

Run each component in a separate terminal on the Pi:
  ros2 launch controller controller.launch.py
  ros2 launch peripherals lidar.launch.py
  ros2 launch rf2o_laser_odometry rf2o_laser_odometry.launch.py
  ros2 launch slam slam_mapping.launch.py          # this file

Run teleop from WSL to drive while mapping:
  ros2 launch peripherals teleop_key_control.launch.py
  # or directly (recommended on WSL without X):
  ros2 run peripherals teleop_key_control

When the map looks complete, save it:
  ros2 service call /map_save_node/save_map std_srvs/srv/Trigger

Map is written to ~/ros2_ws/src/slam/maps/map_01.pgm + map_01.yaml
"""
import os
from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription, LaunchService
from launch.substitutions import LaunchConfiguration
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, OpaqueFunction


def launch_setup(context):
    # FIX: compiled was assigned but never used for path selection — now it drives
    # the same conditional path logic used in slam_base.launch.py.
    # compiled = os.environ.get('need_compile', 'False')

    # FIX: keep as LaunchConfiguration objects (no .perform()) so that CLI
    # overrides (e.g. ros2 launch slam slam_mapping.launch.py scan_topic:=scan)
    # are honoured at runtime.  .perform() is only called where a plain Python
    # string is genuinely required (none needed here — all values flow through
    # launch_arguments into slam_base.launch.py as substitutions).
    use_sim_time = LaunchConfiguration('use_sim_time', default='false')
    scan_topic   = LaunchConfiguration('scan_topic',   default='scan_raw')
    odom_frame   = LaunchConfiguration('odom_frame',   default='odom')
    base_frame   = LaunchConfiguration('base_frame',   default='base_footprint')
    map_frame    = LaunchConfiguration('map_frame',    default='map')

    use_sim_time_arg = DeclareLaunchArgument('use_sim_time', default_value=use_sim_time)
    scan_topic_arg   = DeclareLaunchArgument('scan_topic',   default_value=scan_topic)
    odom_frame_arg   = DeclareLaunchArgument('odom_frame',   default_value=odom_frame)
    base_frame_arg   = DeclareLaunchArgument('base_frame',   default_value=base_frame)
    map_frame_arg    = DeclareLaunchArgument('map_frame',    default_value=map_frame)

    # FIX: mirror the same compiled/source path conditional from slam_base.launch.py
    # so this file doesn't crash when the package isn't installed (compiled == 'False').
    # if compiled == 'True':
    slam_package_path = get_package_share_directory('slam')
    # else:
    #     slam_package_path = '/home/ubuntu/ros2_ws/src/slam'

    slam_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(slam_package_path, 'launch/include/slam_base.launch.py')),
        launch_arguments={
            'use_sim_time': use_sim_time,
            'scan_topic':   scan_topic,
            'odom_frame':   odom_frame,
            'base_frame':   base_frame,
            'map_frame':    map_frame,
            'enable_save':  'true',
        }.items(),
    )

    return [
        use_sim_time_arg,
        scan_topic_arg,
        odom_frame_arg,
        base_frame_arg,
        map_frame_arg,
        slam_launch,
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