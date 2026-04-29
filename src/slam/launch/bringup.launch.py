"""
Bringup launch for lidar SLAM mapping (ROS2 Jazzy).

Pi side (robot):
  ros2 launch slam bringup.launch.py

WSL/desktop side (visualization):
  ros2 launch slam rviz_slam.launch.py

Save map when mapping is complete:
  ros2 run nav2_map_server map_saver_cli \
      -f ~/ros2_ws/src/slam/maps/map_01 \
      --ros-args -p map_subscribe_transient_local:=true
"""
import os
from ament_index_python.packages import get_package_share_directory

from launch_ros.actions import PushRosNamespace
from launch import LaunchDescription, LaunchService
from launch.substitutions import LaunchConfiguration
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.actions import (
    DeclareLaunchArgument,
    GroupAction,
    IncludeLaunchDescription,
    OpaqueFunction,
    TimerAction,
)

def launch_setup(context):
    compiled = os.environ.get('need_compile', 'False')
    sim = LaunchConfiguration('sim', default='false').perform(context)
    robot_name = LaunchConfiguration('robot_name', default=os.environ.get('HOST', '/')).perform(context)
    master_name = LaunchConfiguration('master_name', default=os.environ.get('MASTER', '/')).perform(context)

    sim_arg = DeclareLaunchArgument('sim', default_value=sim)
    robot_name_arg = DeclareLaunchArgument('robot_name', default_value=robot_name)
    master_name_arg = DeclareLaunchArgument('master_name', default_value=master_name)

    frame_prefix = '' if robot_name == '/' else f'{robot_name}/'
    use_sim_time = 'true' if sim == 'true' else 'false'
    map_frame = f'{frame_prefix}map'
    odom_frame = f'{frame_prefix}odom'
    base_frame = f'{frame_prefix}base_footprint'
    scan_topic = f'{frame_prefix}scan_raw'

    if compiled == 'True':
        slam_package_path = get_package_share_directory('slam')
    else:
        slam_package_path = '/home/agent3/ros2_ws/src/slam'

    # Robot base: controller (odometry, motors) + lidar driver
    robot_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(slam_package_path, 'launch/include/robot.launch.py')),
        launch_arguments={
            'sim': sim,
            'master_name': master_name,
            'robot_name': robot_name,
            'use_joy': 'false',
        }.items(),
    )

    # SLAM Toolbox: builds occupancy map from lidar scan + odometry
    slam_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(slam_package_path, 'launch/include/slam_base.launch.py')),
        launch_arguments={
            'use_sim_time': use_sim_time,
            'map_frame': map_frame,
            'odom_frame': odom_frame,
            'base_frame': base_frame,
            'scan_topic': scan_topic,
            'enable_save': 'true',
        }.items(),
    )

    bringup = GroupAction(actions=[
        PushRosNamespace(robot_name),
        robot_launch,
        # Delay SLAM start to allow TF tree to stabilise after robot drivers init
        TimerAction(period=10.0, actions=[slam_launch]),
    ])

    return [sim_arg, robot_name_arg, master_name_arg, bringup]

def generate_launch_description():
    return LaunchDescription([
        OpaqueFunction(function=launch_setup)
    ])

if __name__ == '__main__':
    ld = generate_launch_description()

    ls = LaunchService()
    ls.include_launch_description(ld)
    ls.run()
