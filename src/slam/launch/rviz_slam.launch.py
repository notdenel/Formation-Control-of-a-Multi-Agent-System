import os
from ament_index_python.packages import get_package_share_directory

from launch_ros.actions import Node
from launch import LaunchDescription, LaunchService
from launch.actions import OpaqueFunction
from launch.substitutions import Command

def launch_setup(context):
    compiled = os.environ.get('need_compile', 'False')

    if compiled == 'True':
        slam_pkg = get_package_share_directory('slam')
        desc_pkg = get_package_share_directory('mentorpi_description')
    else:
        slam_pkg = '/home/agent3/ros2_ws/src/slam'
        desc_pkg = '/home/agent3/ros2_ws/src/simulations/mentorpi_description'

    urdf_path = os.path.join(desc_pkg, 'urdf/mentorpi.xacro')
    rviz_config = os.path.join(slam_pkg, 'rviz/slam.rviz')

    robot_description = Command(['xacro ', urdf_path])

    # Run robot_state_publisher locally so RViz gets the URDF and TF tree
    # even when the Pi's Transient Local /robot_description doesn't cross the network
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[{'robot_description': robot_description, 'use_sim_time': False}],
    )

    # Publish zero joint states so RSP produces a complete TF tree
    joint_state_publisher = Node(
        package='joint_state_publisher',
        executable='joint_state_publisher',
        name='joint_state_publisher',
        output='screen',
    )

    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', rviz_config],
        output='screen',
    )

    return [robot_state_publisher, joint_state_publisher, rviz_node]

def generate_launch_description():
    return LaunchDescription([
        OpaqueFunction(function=launch_setup)
    ])

if __name__ == '__main__':
    ld = generate_launch_description()
    ls = LaunchService()
    ls.include_launch_description(ld)
    ls.run()
