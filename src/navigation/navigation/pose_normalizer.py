#!/usr/bin/env python3
"""
pose_normalizer.py
==================
Per-robot node that exposes pose topics from the EKF odom source.

Published topics (all PoseStamped, frame_id=robotX/odom):
  ~/position   EKF-fused odometry pose (primary output)
  ~/odom_pose  Same as position (mirror, kept for compatibility)
  ~/tf_pose    Direct TF lookup robotX/odom→robotX/base_footprint

Run per-robot inside the robot's namespace (real_robot.launch.py does this):
  ros2 run navigation pose_normalizer \\
      --ros-args -r __ns:=/robot1 -p robot_name:=robot1
"""

import rclpy
from rclpy.duration import Duration
from rclpy.node import Node
from rclpy.time import Time
import tf2_ros
from geometry_msgs.msg import PoseStamped
from nav_msgs.msg import Odometry


TF_TIMEOUT = Duration(seconds=0.05)


class PoseNormalizer(Node):
    def __init__(self) -> None:
        super().__init__('pose_normalizer')

        self.declare_parameter('robot_name', 'robot1')
        self._robot      = self.get_parameter('robot_name').value
        self._odom_frame = f'{self._robot}/odom'
        self._base_frame = f'{self._robot}/base_footprint'

        self._tf_buffer   = tf2_ros.Buffer()
        self._tf_listener = tf2_ros.TransformListener(self._tf_buffer, self)

        self.create_subscription(Odometry, 'odom', self._odom_cb, 10)

        self._pub_position  = self.create_publisher(PoseStamped, 'position',  10)
        self._pub_tf_pose   = self.create_publisher(PoseStamped, 'tf_pose',   10)
        self._pub_odom_pose = self.create_publisher(PoseStamped, 'odom_pose', 10)

        self.create_timer(0.1, self._timer_cb)

        self.get_logger().info(
            f'[{self._robot}] pose_normalizer ready\n'
            f'  /{self._robot}/position   ← EKF odom\n'
            f'  /{self._robot}/odom_pose  ← EKF odom (mirror)\n'
            f'  /{self._robot}/tf_pose    ← TF {self._odom_frame}→{self._base_frame}'
        )

    def _odom_cb(self, msg: Odometry) -> None:
        out = PoseStamped()
        out.header.stamp    = msg.header.stamp
        out.header.frame_id = msg.header.frame_id  # robotX/odom
        out.pose            = msg.pose.pose
        self._pub_position.publish(out)
        self._pub_odom_pose.publish(out)

    def _timer_cb(self) -> None:
        try:
            t = self._tf_buffer.lookup_transform(
                self._odom_frame, self._base_frame, Time(), timeout=TF_TIMEOUT)
        except (tf2_ros.LookupException, tf2_ros.ExtrapolationException,
                tf2_ros.ConnectivityException):
            return

        out = PoseStamped()
        out.header.stamp    = t.header.stamp
        out.header.frame_id = self._odom_frame
        out.pose.position.x = t.transform.translation.x
        out.pose.position.y = t.transform.translation.y
        out.pose.position.z = t.transform.translation.z
        out.pose.orientation = t.transform.rotation
        self._pub_tf_pose.publish(out)


def main(args=None) -> None:
    rclpy.init(args=args)
    node = PoseNormalizer()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
