from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument, EmitEvent, RegisterEventHandler
from launch.event_handlers import OnProcessExit
from launch.events import Shutdown
from launch import LaunchDescription, LaunchService
from launch.substitutions import LaunchConfiguration

def generate_launch_description():
    lidar_frame = LaunchConfiguration('lidar_frame', default='base_laser')
    scan_raw = LaunchConfiguration('scan_raw', default='scan_raw')
    lidar_frame_arg = DeclareLaunchArgument('lidar_frame', default_value=lidar_frame)
    scan_raw_arg = DeclareLaunchArgument('scan_raw', default_value=scan_raw)

    ld19_node = Node(
        package='ldlidar_stl_ros2',
        executable='ldlidar_stl_ros2_node',
        name='LD19',
        output='screen',
        parameters=[
            {
                'topic_name': 'scan',
                'product_name': 'LDLiDAR_LD19',
                'port_baudrate': 230400,
                'port_name': '/dev/ldlidar',
                'frame_id': lidar_frame,
                'laser_scan_dir': True,
                'enable_angle_crop_func': False,
                'angle_crop_min': 135.0,
                'angle_crop_max': 225.0,
                'publish_rate': 30.0,
            }
        ],
        remappings=[('scan', scan_raw)]
    )

    # If the lidar node exits for any reason (crash or normal shutdown), propagate
    # a Shutdown event so no other node keeps running without sensor data.
    # During a normal Ctrl-C the launch system is already shutting down, so the
    # duplicate Shutdown event is a harmless no-op.
    lidar_exit_handler = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=ld19_node,
            on_exit=[EmitEvent(event=Shutdown())]
        )
    )

    return LaunchDescription([
        lidar_frame_arg,
        scan_raw_arg,
        ld19_node,
        lidar_exit_handler,
    ])

if __name__ == '__main__':
    ld = generate_launch_description()

    ls = LaunchService()
    ls.include_launch_description(ld)
    ls.run()
