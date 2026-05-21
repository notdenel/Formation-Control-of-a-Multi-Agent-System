"""
odom_bridge.launch.py
=====================
Starts a domain_bridge process for ONE robot that bridges the minimum set
of topics needed for distributed aggregation and WSL observation.

What is bridged for robotX (private domain D → fleet domain 10, and back):

  private → fleet (10):
    /robotX/odom        own EKF-fused odometry  (position + velocity)

  fleet (10) → private:
    /robotY/odom        peer Y position           (for on-robot aggregation)
    /robotZ/odom        peer Z position           (for on-robot aggregation)

Nothing else crosses the boundary — scan, TF, IMU, costmap, and cmd_vel all
stay local.  Aggregation runs on each robot in its private domain so cmd_vel
never needs to be bridged.

Usage (called automatically by real_robot.launch.py):
    ros2 launch navigation odom_bridge.launch.py robot_name:=robot1
    ros2 launch navigation odom_bridge.launch.py robot_name:=robot2
    ros2 launch navigation odom_bridge.launch.py robot_name:=robot3

Domain mapping:
    robot1 private domain: 11
    robot2 private domain: 12
    robot3 private domain: 13
    fleet / WSL domain:    10
"""

import os
import tempfile

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


_ROBOT_DOMAINS = {
    'robot1': 11,
    'robot2': 12,
    'robot3': 13,
}


def _launch_setup(context, *args, **kwargs):
    robot_name = LaunchConfiguration('robot_name').perform(context)

    if robot_name not in _ROBOT_DOMAINS:
        raise ValueError(
            f'odom_bridge.launch.py: unknown robot_name {robot_name!r}; '
            f'expected one of {list(_ROBOT_DOMAINS)}.')

    private_domain = _ROBOT_DOMAINS[robot_name]
    peers = sorted(ns for ns in _ROBOT_DOMAINS if ns != robot_name)

    pkg_share = get_package_share_directory('navigation')
    template_path = os.path.join(pkg_share, 'config', 'odom_bridge.yaml')

    with open(template_path, 'r') as f:
        rendered = (
            f.read()
            .replace('__ROBOT_NS__', robot_name)
            .replace('__PRIVATE_DOMAIN__', str(private_domain))
            .replace('__PEER1_NS__', peers[0])
            .replace('__PEER2_NS__', peers[1])
        )

    tmp = tempfile.NamedTemporaryFile(
        mode='w', delete=False, suffix='.yaml',
        prefix=f'odom_bridge_{robot_name}_',
    )
    tmp.write(rendered)
    tmp.flush()
    tmp.close()

    dds_cfg = os.path.join(pkg_share, 'config', 'cyclone_dds.xml')

    return [Node(
        package='domain_bridge',
        executable='domain_bridge',
        name=f'domain_bridge_{robot_name}',
        arguments=[tmp.name],
        output='screen',
        additional_env={
            'CYCLONEDDS_URI': f'file://{dds_cfg}',
            'ROS_AUTOMATIC_DISCOVERY_RANGE': 'SUBNET',
        },
    )]


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument(
            'robot_name', default_value='robot1',
            description='Robot namespace: robot1 | robot2 | robot3'),
        OpaqueFunction(function=_launch_setup),
    ])
