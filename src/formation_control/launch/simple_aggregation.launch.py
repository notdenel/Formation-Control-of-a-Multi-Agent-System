from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node, PushRosNamespace


def generate_launch_description():
    robot_name = LaunchConfiguration('robot_name')

    return LaunchDescription([
        DeclareLaunchArgument(
            'robot_name',
            default_value='',
            description='Robot namespace, e.g. robot1, robot2, robot3. Empty means no namespace.'),
        DeclareLaunchArgument('goal_x',          default_value='1.0',
                              description='Goal X in the selected odom/map frame, metres'),
        DeclareLaunchArgument('goal_y',          default_value='0.0',
                              description='Goal Y in the selected odom/map frame, metres'),
        DeclareLaunchArgument('max_speed',       default_value='0.25',
                              description='Maximum linear speed in m/s'),
        DeclareLaunchArgument('goal_tolerance',  default_value='0.20',
                              description='Stop radius around goal in metres'),
        DeclareLaunchArgument('ga',              default_value='1.0',
                              description='Proportional gain: speed = ga * distance, capped'),
        DeclareLaunchArgument('odom_topic',      default_value='odom',
                              description='Relative odometry topic. With robot_name:=robot2, resolves to /robot2/odom'),
        DeclareLaunchArgument('cmd_vel_topic',   default_value='controller/cmd_vel',
                              description='Relative Twist command topic. With robot_name:=robot2, resolves to /robot2/controller/cmd_vel'),

        GroupAction([
            PushRosNamespace(robot_name),
            Node(
                package='formation_control',
                executable='goto_goal_node',
                name='goto_goal',
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
        ]),
    ])
