import os
from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription, LaunchService
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node, PushRosNamespace
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.actions import (
    DeclareLaunchArgument, GroupAction, IncludeLaunchDescription, OpaqueFunction,
)


def launch_setup(context):
    namespace     = LaunchConfiguration('namespace').perform(context)
    use_namespace = LaunchConfiguration('use_namespace').perform(context)
    odom_frame    = LaunchConfiguration('odom_frame').perform(context)
    base_frame    = LaunchConfiguration('base_frame').perform(context)
    imu_frame     = LaunchConfiguration('imu_frame').perform(context)

    robot_controller_pkg = get_package_share_directory('ros_robot_controller')
    controller_pkg       = get_package_share_directory('controller')

    # Hardware driver — subscribes to ~/set_motor, ~/set_led etc. (tilde topics).
    # Placing it in the robot namespace makes those topics resolve to
    # /robotX/ros_robot_controller/set_motor, which odom_publisher publishes to
    # via the relative "ros_robot_controller/set_motor" topic (also in namespace).
    robot_controller_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(robot_controller_pkg, 'launch/ros_robot_controller.launch.py')
        ),
        launch_arguments={'imu_frame': imu_frame}.items(),
    )

    # Motor driver + wheel odometry publisher.
    # Subscribes to "controller/cmd_vel" (relative).
    # In namespace /robotX this becomes /robotX/controller/cmd_vel, so only
    # teleop that publishes to /robotX/controller/cmd_vel drives this robot.
    odom_publisher_node = Node(
        package='controller',
        executable='odom_publisher',
        name='odom_publisher',
        output='screen',
        parameters=[
            os.path.join(controller_pkg, 'config/calibrate_params.yaml'),
            {
                'base_frame_id': base_frame,
                'odom_frame_id': odom_frame,
                'pub_odom_topic': True,
            },
        ],
    )

    nodes = [robot_controller_launch, odom_publisher_node]

    if use_namespace == 'true' and namespace:
        # Wrap both nodes in the robot namespace so cmd_vel and motor topics
        # are isolated per robot — prevents cross-robot teleop bleed.
        return [GroupAction([PushRosNamespace(namespace)] + nodes)]

    return nodes


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('namespace',     default_value=''),
        DeclareLaunchArgument('use_namespace', default_value='false'),
        DeclareLaunchArgument('odom_frame',    default_value='odom'),
        DeclareLaunchArgument('base_frame',    default_value='base_footprint'),
        DeclareLaunchArgument('imu_frame',     default_value='imu_link'),
        DeclareLaunchArgument('frame_prefix',  default_value=''),
        OpaqueFunction(function=launch_setup),
    ])


if __name__ == '__main__':
    ld = generate_launch_description()
    ls = LaunchService()
    ls.include_launch_description(ld)
    ls.run()
