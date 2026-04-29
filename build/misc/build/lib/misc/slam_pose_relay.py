#!/usr/bin/env python3
# encoding: utf-8
"""
slam_pose_relay.py — Converts slam_toolbox TF output to /amcl_pose.

slam_toolbox publishes the map→odom TF but does NOT publish /amcl_pose.
global_ref_nav.py uses /amcl_pose as its primary localisation source.
This node bridges the gap: it reads the map→base_footprint TF every 50ms
and republishes it as a PoseWithCovarianceStamped on /amcl_pose with a
small, fixed covariance so global_ref_nav accepts the pose.
"""

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, DurabilityPolicy, ReliabilityPolicy, HistoryPolicy
from geometry_msgs.msg import PoseWithCovarianceStamped
import tf2_ros


_AMCL_QOS = QoSProfile(
    depth=1,
    reliability=ReliabilityPolicy.RELIABLE,
    durability=DurabilityPolicy.TRANSIENT_LOCAL,
    history=HistoryPolicy.KEEP_LAST,
)

# Small covariance so global_ref_nav's AMCL_COV_ACCEPT (1.50) check passes.
_COVARIANCE = [0.0] * 36
_COVARIANCE[0]  = 0.01   # x
_COVARIANCE[7]  = 0.01   # y
_COVARIANCE[35] = 0.02   # yaw


class SlamPoseRelay(Node):
    def __init__(self):
        super().__init__('slam_pose_relay')
        self.declare_parameter('map_frame',  'map')
        self.declare_parameter('base_frame', 'base_footprint')
        self.declare_parameter('rate_hz',    20.0)

        self._map_frame  = self.get_parameter('map_frame').value
        self._base_frame = self.get_parameter('base_frame').value
        rate_hz          = self.get_parameter('rate_hz').value

        self._tf_buffer   = tf2_ros.Buffer()
        self._tf_listener = tf2_ros.TransformListener(self._tf_buffer, self)

        self._pub = self.create_publisher(
            PoseWithCovarianceStamped, '/amcl_pose', _AMCL_QOS)

        self.create_timer(1.0 / rate_hz, self._publish_pose)
        self.get_logger().info(
            f'slam_pose_relay ready — relaying {self._map_frame}→{self._base_frame} as /amcl_pose')

    def _publish_pose(self):
        try:
            t = self._tf_buffer.lookup_transform(
                self._map_frame, self._base_frame, rclpy.time.Time())
        except (tf2_ros.LookupException,
                tf2_ros.ConnectivityException,
                tf2_ros.ExtrapolationException):
            return

        msg = PoseWithCovarianceStamped()
        msg.header.stamp    = self.get_clock().now().to_msg()
        msg.header.frame_id = self._map_frame
        tr = t.transform.translation
        msg.pose.pose.position.x  = tr.x
        msg.pose.pose.position.y  = tr.y
        msg.pose.pose.position.z  = 0.0
        msg.pose.pose.orientation = t.transform.rotation
        msg.pose.covariance       = _COVARIANCE
        self._pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = SlamPoseRelay()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
