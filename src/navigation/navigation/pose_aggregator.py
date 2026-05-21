#!/usr/bin/env python3
"""
pose_aggregator.py
==================
Runs on the WSL coordinator (domain 10).  Dynamically discovers active robots
by scanning for /robotX/odom publishers and subscribing only when a live
publisher exists — no phantom topics for robots that are not running.

Topics subscribed (created on demand):
  /robotX/odom  (nav_msgs/Odometry)
  These are bridged from each robot's private domain via odom_bridge.

Topics published:
  /global_robot_states  (geometry_msgs/PoseArray, frame_id=odom)
    poses[i] = robot i in sorted discovery order.
    Missing poses have position.z = -1.0 as a sentinel.
"""

import re

import rclpy
from rclpy.node import Node
from rclpy.qos import (
    QoSProfile, DurabilityPolicy, ReliabilityPolicy, HistoryPolicy,
)
from geometry_msgs.msg import PoseArray, Pose
from nav_msgs.msg import Odometry


ODOM_QOS = QoSProfile(
    depth=1,
    reliability=ReliabilityPolicy.RELIABLE,
    durability=DurabilityPolicy.VOLATILE,
    history=HistoryPolicy.KEEP_LAST,
)

_ODOM_PATTERN = re.compile(r'^(/robot\w+)/odom$')


class PoseAggregator(Node):
    def __init__(self):
        super().__init__('pose_aggregator')

        self._poses: dict[str, Pose] = {}
        self._subs: dict[str, rclpy.node.Subscription] = {}

        self._pub = self.create_publisher(PoseArray, '/global_robot_states', 10)
        self.create_timer(0.2, self._publish)
        self.create_timer(2.0, self._discover)

        self.get_logger().info(
            'pose_aggregator ready — scanning for active robots on domain 10')

    def _discover(self) -> None:
        """Subscribe to odom for any robot that has a live publisher."""
        for topic_name, _ in self.get_topic_names_and_types():
            m = _ODOM_PATTERN.match(topic_name)
            if not m:
                continue
            ns = m.group(1)
            if ns in self._subs:
                continue
            if self.count_publishers(topic_name) == 0:
                continue
            self._subs[ns] = self.create_subscription(
                Odometry,
                topic_name,
                lambda msg, n=ns: self._odom_cb(msg, n),
                ODOM_QOS,
            )
            self.get_logger().info(
                f'Discovered robot: {ns}  (tracking {sorted(self._subs)})')

    def _odom_cb(self, msg: Odometry, robot_name: str) -> None:
        first = robot_name not in self._poses
        self._poses[robot_name] = msg.pose.pose
        if first:
            self.get_logger().info(f'First pose received from {robot_name}')

    def _publish(self) -> None:
        if not self._subs:
            return
        msg = PoseArray()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'odom'
        for ns in sorted(self._subs):
            if ns in self._poses:
                msg.poses.append(self._poses[ns])
            else:
                sentinel = Pose()
                sentinel.position.z = -1.0
                msg.poses.append(sentinel)
        self._pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = PoseAggregator()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
