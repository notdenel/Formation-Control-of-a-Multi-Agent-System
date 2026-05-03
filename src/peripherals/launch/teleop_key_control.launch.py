from launch.actions import DeclareLaunchArgument
from launch import LaunchDescription, LaunchService
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    robot_name_arg = DeclareLaunchArgument(
        'robot_name',
        default_value='robot1',
        description='Robot namespace (e.g. robot1, robot2)'
    )

    robot_name = LaunchConfiguration('robot_name')

    teleop_key_control_node = Node(
        package='peripherals',
        executable='teleop_key_control',
        name='teleop_key_control',
        namespace=robot_name,
        output='screen',
        remappings=[('cmd_vel', f'/{os.environ.get("ROBOT_NAME", "robot1")}/cmd_vel')]
    )

    ld = LaunchDescription()
    ld.add_action(robot_name_arg)
    ld.add_action(teleop_key_control_node)

    return ld

if __name__ == '__main__':
    # 创建一个LaunchDescription对象(create a LaunchDescription object)
    ld = generate_launch_description()

    ls = LaunchService()
    ls.include_launch_description(ld)
    ls.run()
