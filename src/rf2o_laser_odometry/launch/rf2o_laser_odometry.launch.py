from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node, PushRosNamespace


def launch_setup(context, *args, **kwargs):
    namespace      = LaunchConfiguration('namespace').perform(context)
    scan_raw       = LaunchConfiguration('scan_raw').perform(context)
    odom_topic     = LaunchConfiguration('odom_topic').perform(context)
    base_frame_raw = LaunchConfiguration('base_frame_id').perform(context)
    odom_frame_raw = LaunchConfiguration('odom_frame_id').perform(context)
    publish_tf     = LaunchConfiguration('publish_tf').perform(context)
    freq           = LaunchConfiguration('freq').perform(context)

    def qualify(frame):
        if namespace and '/' not in frame:
            return f'{namespace}/{frame}'
        return frame

    base_frame_id = qualify(base_frame_raw)
    odom_frame_id = qualify(odom_frame_raw)

    rf2o_node = Node(
        package='rf2o_laser_odometry',
        executable='rf2o_laser_odometry_node',
        name='rf2o_laser_odometry',
        output='screen',
        parameters=[{
            'laser_scan_topic':    scan_raw,      # relative -> /robotX/scan_raw
            'odom_topic':          odom_topic,    # relative -> /robotX/odom_rf2o
            'publish_tf':          publish_tf.lower() == 'true',
            'base_frame_id':       base_frame_id, # fully qualified
            'odom_frame_id':       odom_frame_id, # fully qualified
            'init_pose_from_topic': '',
            'freq':                float(freq),
        }],
    )

    grouped = GroupAction([
        PushRosNamespace(namespace) if namespace else GroupAction([]),
        rf2o_node,
    ])

    return [grouped]


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('namespace',     default_value=''),
        DeclareLaunchArgument('scan_raw',      default_value='scan_raw'),
        DeclareLaunchArgument('odom_topic',    default_value='odom_rf2o'),
        DeclareLaunchArgument('base_frame_id', default_value='base_footprint'),
        DeclareLaunchArgument('odom_frame_id', default_value='odom'),
        DeclareLaunchArgument('publish_tf',    default_value='false'),
        DeclareLaunchArgument('freq',          default_value='10.0'),
        OpaqueFunction(function=launch_setup),
    ])