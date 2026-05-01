"""
single_robot.launch.py
======================
AMCL localization stack for ONE robot: map_server + amcl + lifecycle_manager.
Use this on a real Pi alongside the hardware stack.

  ros2 launch multi_robot_bringup single_robot.launch.py robot_name:=robot1

Hardware must be started separately:
  ros2 launch multi_robot_bringup real_robot.launch.py robot_name:=robot1

Expected TF after both stacks are up:
  map → robot1/odom  (AMCL)
   └── robot1/base_footprint  (EKF)
        └── robot1/lidar_frame (static TF from this launch)

AMCL needs an initial pose to converge:
  ros2 topic pub --once /robot1/initialpose \\
      geometry_msgs/PoseWithCovarianceStamped \\
      '{header:{frame_id:map},pose:{pose:{position:{x:0.0,y:0.0}}}}'
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node, PushRosNamespace


def launch_setup(context, *args, **kwargs):
    robot_name   = LaunchConfiguration('robot_name').perform(context)
    use_sim_time = LaunchConfiguration('use_sim_time').perform(context)
    lidar_frame  = LaunchConfiguration('lidar_frame').perform(context)

    pkg_dir     = get_package_share_directory('multi_robot_bringup')
    map_yaml    = os.path.join(pkg_dir, 'config', 'maps', 'map_01.yaml')
    params_file = os.path.join(pkg_dir, 'config', f'nav2_params_{robot_name}.yaml')

    use_sim_time_bool = use_sim_time.lower() == 'true'

    robot_group = GroupAction([
        PushRosNamespace(robot_name),

        Node(
            package='nav2_map_server',
            executable='map_server',
            name='map_server',
            output='screen',
            parameters=[params_file, {
                'yaml_filename': map_yaml,
                'use_sim_time': use_sim_time_bool,
            }],
        ),

        Node(
            package='nav2_amcl',
            executable='amcl',
            name='amcl',
            output='screen',
            parameters=[params_file, {
                'use_sim_time': use_sim_time_bool,
            }],
        ),

        Node(
            package='nav2_lifecycle_manager',
            executable='lifecycle_manager',
            name='lifecycle_manager_localization',
            output='screen',
            parameters=[{
                'use_sim_time': use_sim_time_bool,
                'autostart':    True,
                'node_names':   ['map_server', 'amcl'],
                'bond_timeout': 4.0,
            }],
        ),

        # Static TF: base_footprint → lidar_frame
        # Frame IDs must use full namespace prefix (TF is never auto-namespaced)
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='lidar_static_tf',
            output='screen',
            arguments=[
                '--x', '0.0', '--y', '0.0', '--z', '0.10',
                '--roll', '0.0', '--pitch', '0.0', '--yaw', '0.0',
                '--frame-id', f'{robot_name}/base_footprint',
                '--child-frame-id', f'{robot_name}/{lidar_frame}',
            ],
        ),
    ])

    return [robot_group]


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument(
            'robot_name', default_value='robot1',
            description='Robot namespace (robot1 | robot2 | robot3)'),
        DeclareLaunchArgument(
            'use_sim_time', default_value='false'),
        DeclareLaunchArgument(
            'lidar_frame', default_value='lidar_frame',
            description='Lidar TF frame name suffix after robot_name/'),
        OpaqueFunction(function=launch_setup),
    ])
