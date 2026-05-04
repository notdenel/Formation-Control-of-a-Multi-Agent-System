import os
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import TimerAction
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    calib_file_path = os.path.join(
        get_package_share_directory('calibration'), 'config/imu_calib.yaml')

    imu_calib_node = Node(
        package='calibration',
        executable='apply_calib',
        name='imu_calib',
        output='screen',
        parameters=[{'calib_file': calib_file_path}],
        remappings=[
            ('raw', '/ros_robot_controller/imu_raw'),
            ('corrected', 'imu_corrected'),
        ]
    )

    imu_filter_node = Node(
        package='imu_complementary_filter',
        executable='complementary_filter_node',
        name='imu_filter',
        output='screen',
        parameters=[
            {
                'use_mag': True,
                'do_bias_estimation': True,
                'do_adaptive_gain': True,
                'publish_debug_topics': True
            }
        ],
        remappings=[
            ('/tf', 'tf'),
            ('/imu/data_raw', 'imu_corrected'),
            ('imu/data', 'imu')
        ]
    )

    return LaunchDescription([
        TimerAction(
            period=5.0,
            actions=[imu_calib_node, imu_filter_node]
        )
    ])

if __name__ == '__main__':
    from launch import LaunchService
    ld = generate_launch_description()

    ls = LaunchService()
    ls.include_launch_description(ld)
    ls.run()
