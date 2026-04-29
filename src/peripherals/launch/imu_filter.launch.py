from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import TimerAction


def generate_launch_description():
    # imu_complementary_filter: reads raw accel+gyro, outputs fused orientation.
    # Input topic remapped directly from the hardware driver's raw IMU topic.
    # imu_calib (apply_calib) is not available in ROS 2 Jazzy apt repositories,
    # so raw data goes straight to the filter; add calibration here if you
    # build imu_calib from source later.
    imu_filter_node = Node(
        package='imu_complementary_filter',
        executable='complementary_filter_node',
        name='imu_filter',
        output='screen',
        parameters=[
            {
                'use_mag': False,
                'do_bias_estimation': True,
                'do_adaptive_gain': True,
                'publish_debug_topics': False,
            }
        ],
        remappings=[
            ('/imu/data_raw', '/ros_robot_controller/imu_raw'),
            ('imu/data', 'imu'),
        ]
    )

    return LaunchDescription([
        TimerAction(
            period=3.0,
            actions=[imu_filter_node]
        )
    ])


if __name__ == '__main__':
    from launch import LaunchService
    ld = generate_launch_description()

    ls = LaunchService()
    ls.include_launch_description(ld)
    ls.run()
