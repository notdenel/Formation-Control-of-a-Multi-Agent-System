"""
odom_bridge.launch.py
=====================
Run on EACH robot to bridge odom between its private ROS_DOMAIN_ID and
the fleet domain (10).

What the bridge does for robotX (private domain D):
  /robotX/odom  :  D  → 10   (share own position with the fleet)
  /robotY/odom  :  10 → D    (receive peer Y position locally)
  /robotZ/odom  :  10 → D    (receive peer Z position locally)

The aggregation node then runs ON the robot in domain D, subscribes to all
three /robotX/odom, /robotY/odom, /robotZ/odom topics locally, computes the
APF force, and publishes /robotX/controller/cmd_vel in domain D — no cmd_vel
bridge needed.

Usage:
    ros2 launch navigation odom_bridge.launch.py robot_name:=robot1
    ros2 launch navigation odom_bridge.launch.py robot_name:=robot2
    ros2 launch navigation odom_bridge.launch.py robot_name:=robot3
"""

import os
import tempfile

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


_ROBOTS = {
    'robot1': 11,
    'robot2': 12,
    'robot3': 13,
}


def _launch_setup(context, *args, **kwargs):
    robot_name = LaunchConfiguration('robot_name').perform(context)
    if robot_name not in _ROBOTS:
        raise ValueError(
            f'odom_bridge.launch.py: unknown robot_name {robot_name!r}; '
            f'expected one of {list(_ROBOTS)}.')

    private_domain = _ROBOTS[robot_name]
    peers = [ns for ns in _ROBOTS if ns != robot_name]   # always exactly 2

    pkg_share = get_package_share_directory('navigation')
    template = os.path.join(pkg_share, 'config', 'odom_bridge.yaml')
    with open(template, 'r') as f:
        rendered = (
            f.read()
            .replace('__ROBOT_NS__',       robot_name)
            .replace('__PRIVATE_DOMAIN__', str(private_domain))
            .replace('__PEER1_NS__',       peers[0])
            .replace('__PEER2_NS__',       peers[1])
        )

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
