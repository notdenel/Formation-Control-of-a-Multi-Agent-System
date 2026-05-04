"""
single_robot.launch.py
======================
AMCL localization stack for ONE robot: map_server + amcl + lifecycle_manager.
Use this on a real Pi alongside the hardware stack.

  ros2 launch multi_robot_bringup single_robot.launch.py robot_name:=robot1

  # Use a specific map (filename without extension, from config/maps/):
  ros2 launch multi_robot_bringup single_robot.launch.py robot_name:=robot1 map:=map_01

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
from launch.actions import DeclareLaunchArgument, GroupAction, OpaqueFunction, TimerAction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node, PushRosNamespace


# Match peripherals/lidar.launch.py and slam/launch/slam.launch.py — the
# laser_filters chain is disabled, so the only published topic is scan_raw.
# Both AMCL and the costmap subscribe to this name (relative → /robotX/scan_raw).
_SCAN_TOPIC = 'scan_raw'


def launch_setup(context, *args, **kwargs):
    robot_name   = LaunchConfiguration('robot_name').perform(context)
    use_sim_time = LaunchConfiguration('use_sim_time').perform(context)
    lidar_frame  = LaunchConfiguration('lidar_frame').perform(context)
    map_name     = LaunchConfiguration('map').perform(context)
    scan_topic   = LaunchConfiguration('scan_topic').perform(context)

    pkg_dir     = get_package_share_directory('multi_robot_bringup')
    map_yaml    = os.path.join(pkg_dir, 'config', 'maps', f'{map_name}.yaml')
    params_file = os.path.join(pkg_dir, 'config', f'nav2_params_{robot_name}.yaml')

    if not os.path.isfile(map_yaml):
        raise FileNotFoundError(
            f"Map YAML not found: {map_yaml}. Place a SLAM-built map at "
            f"config/maps/{map_name}.yaml inside multi_robot_bringup."
        )

    use_sim_time_bool = use_sim_time.lower() == 'true'

    # AMCL/map_server overrides applied AFTER nav2_params_<robot>.yaml so the
    # robot-specific YAML supplies node-tunable defaults (alphas, ranges, etc.)
    # and the launch line guarantees the topic + map_yaml are correct.
    map_overrides = {
        'use_sim_time':  use_sim_time_bool,
        'yaml_filename': map_yaml,                 # absolute path; never empty
        'topic_name':    'map',                    # /{robot_name}/map
        'frame_id':      'map',                    # global, never namespaced
    }
    amcl_overrides = {
        'use_sim_time':   use_sim_time_bool,
        'scan_topic':     scan_topic,              # /{robot_name}/scan_raw
        'odom_frame_id':  f'{robot_name}/odom',
        'base_frame_id':  f'{robot_name}/base_footprint',
        'global_frame_id': 'map',
        'tf_broadcast':   True,
    }

    # nav2_amcl in Jazzy uses a sensor-data QoS (best-effort, depth=10) on the
    # scan subscription by default. The LD19 lidar publishes RELIABLE; that is
    # request-side compatible (reliable pub → best-effort sub is allowed), so
    # AMCL receives messages without QoS overrides. We make the durability
    # transient_local on /map and reliable on scan_raw at the publisher side
    # (in lidar.launch.py / map_server defaults), which is what nav2 expects.

    nodes = [
        # Map server — serves /{robot_name}/map at TRANSIENT_LOCAL, latched.
        Node(
            package='nav2_map_server',
            executable='map_server',
            name='map_server',
            output='screen',
            parameters=[params_file, map_overrides],
        ),

        # AMCL — publishes TF map → {robot_name}/odom and /{robot_name}/amcl_pose.
        Node(
            package='nav2_amcl',
            executable='amcl',
            name='amcl',
            output='screen',
            parameters=[params_file, amcl_overrides],
        ),

        # Static TF: base_footprint → lidar_frame.
        # Frame IDs are NEVER auto-namespaced by ROS — must be fully qualified.
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
    ]

    # Lifecycle manager: configures + activates map_server then amcl.
    # bond_timeout=0.0 disables the heartbeat check — matches slam_base.launch.py
    # and avoids the default 4 s timeout aborting bringup if a node is slow.
    # Delayed 2 s so map_server and amcl are fully registered before configure.
    lifecycle_manager = TimerAction(
        period=2.0,
        actions=[Node(
            package='nav2_lifecycle_manager',
            executable='lifecycle_manager',
            name='lifecycle_manager_localization',
            output='screen',
            parameters=[{
                'use_sim_time': use_sim_time_bool,
                'autostart':    True,
                'node_names':   ['map_server', 'amcl'],
                'bond_timeout': 0.0,
            }],
        )],
    )

    robot_group = GroupAction([
        PushRosNamespace(robot_name),
        *nodes,
        lifecycle_manager,
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
        DeclareLaunchArgument(
            'map', default_value='map_01',
            description='Map filename without extension, relative to config/maps/'),
        DeclareLaunchArgument(
            'scan_topic', default_value=_SCAN_TOPIC,
            description='Scan topic AMCL subscribes to; matches lidar.launch.py output'),
        OpaqueFunction(function=launch_setup),
    ])
