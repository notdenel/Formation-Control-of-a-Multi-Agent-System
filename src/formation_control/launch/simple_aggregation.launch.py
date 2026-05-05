from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('goal_x',          default_value='1.0',
                              description='Goal X in odom frame (metres)'),
        DeclareLaunchArgument('goal_y',          default_value='0.0',
                              description='Goal Y in odom frame (metres)'),
        DeclareLaunchArgument('max_speed',       default_value='0.25',
                              description='Maximum linear speed (m/s)'),
        DeclareLaunchArgument('goal_tolerance',  default_value='0.20',
                              description='Stop radius around goal (metres)'),
        DeclareLaunchArgument('ga',              default_value='1.0',
                              description='Proportional gain (speed = ga * distance, capped)'),
        DeclareLaunchArgument('odom_topic',      default_value='/odom',
                              description='Odometry topic to localise from'),
        DeclareLaunchArgument('cmd_vel_topic',   default_value='controller/cmd_vel',
                              description='Twist command topic consumed by the motor driver'),

        Node(
            package='simple_aggregation',
            executable='simple_aggregation',
            name='simple_aggregation',
            parameters=[{
                'goal_x':         LaunchConfiguration('goal_x'),
                'goal_y':         LaunchConfiguration('goal_y'),
                'max_speed':      LaunchConfiguration('max_speed'),
                'goal_tolerance': LaunchConfiguration('goal_tolerance'),
                'ga':             LaunchConfiguration('ga'),
                'odom_topic':     LaunchConfiguration('odom_topic'),
                'cmd_vel_topic':  LaunchConfiguration('cmd_vel_topic'),
            }],
            output='screen',
        ),
    ])
