"""
odom_bridge.launch.py
=====================
Run on EACH robot to bridge a tiny set of topics between the robot's
private ROS_DOMAIN_ID and the fleet ROS_DOMAIN_ID (10).

Usage:
    ros2 launch navigation odom_bridge.launch.py robot_name:=robot1
    ros2 launch navigation odom_bridge.launch.py robot_name:=robot2
    ros2 launch navigation odom_bridge.launch.py robot_name:=robot3

The robot's private domain is inferred from robot_name:
    robot1 -> 11
    robot2 -> 12
    robot3 -> 13

IMPORTANT: domain_bridge joins BOTH domains itself based on the YAML
config, so the shell ROS_DOMAIN_ID for this launch does not matter. The
launch file copies the packaged YAML to a temp file with the namespace
and private-domain placeholders filled in.
"""

import os
import tempfile

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


_PRIVATE_DOMAIN = {'robot1': 11, 'robot2': 12, 'robot3': 13}


def _launch_setup(context, *args, **kwargs):
    robot_name = LaunchConfiguration('robot_name').perform(context)
    if robot_name not in _PRIVATE_DOMAIN:
        raise ValueError(
            f'odom_bridge.launch.py: unknown robot_name {robot_name!r}; '
            f'expected one of {list(_PRIVATE_DOMAIN)}.')
    private_domain = _PRIVATE_DOMAIN[robot_name]

    pkg_share = get_package_share_directory('navigation')
    template = os.path.join(pkg_share, 'config', 'odom_bridge.yaml')
    with open(template, 'r') as f:
        rendered = f.read().replace(
            '__ROBOT_NS__', robot_name
        ).replace('__PRIVATE_DOMAIN__', str(private_domain))

    tmp = tempfile.NamedTemporaryFile(
        mode='w', delete=False, suffix='.yaml',
        prefix=f'odom_bridge_{robot_name}_')
    tmp.write(rendered)
    tmp.flush()
    tmp.close()

    return [Node(
        package='domain_bridge',
        executable='domain_bridge',
        name=f'domain_bridge_{robot_name}',
        arguments=[tmp.name],
        output='screen',
    )]


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument(
            'robot_name', default_value='robot1',
            description='Robot namespace: robot1 | robot2 | robot3'),
        OpaqueFunction(function=_launch_setup),
    ])
