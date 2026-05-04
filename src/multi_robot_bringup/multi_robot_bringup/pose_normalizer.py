#!/usr/bin/env python3
"""
pose_normalizer.py
==================
Per-robot node that exposes three pose topics from three independent sources
so consumers can compare them and choose the right one for their use case.

Published topics (all PoseStamped, frame_id=map):
  ~/position   AMCL pose — authoritative global localization (particle filter)
  ~/tf_pose    Direct TF lookup map→robotX/base_footprint (combined chain)
  ~/odom_pose  EKF Odometry pose projected into map via TF (dead-reckoning view)

The gap between position and odom_pose reveals accumulated AMCL correction:
  - small gap  → odometry and AMCL agree, robot hasn't drifted much
  - large gap  → significant dead-reckoning drift; AMCL is compensating heavily

Diagnosing drift across robots:
  ros2 topic echo /robot1/position
  ros2 topic echo /robot1/odom_pose    # compare — larger gap = more drift
  ros2 topic echo /robot1/tf_pose      # must track position closely (TF = AMCL)

Run per-robot inside the robot's namespace (real_robot.launch.py does this):
  ros2 run multi_robot_bringup pose_normalizer \\
      --ros-args -r __ns:=/robot1 -p robot_name:=robot1
"""

import rclpy
from rclpy.duration import Duration
from rclpy.node import Node
from rclpy.qos import (
    QoSProfile, DurabilityPolicy, ReliabilityPolicy, HistoryPolicy,
)
from rclpy.time import Time
import tf2_ros
import tf2_geometry_msgs  # noqa: F401 — registers PoseStamped do_transform
from geometry_msgs.msg import PoseStamped, PoseWithCovarianceStamped
from nav_msgs.msg import Odometry


AMCL_QOS = QoSProfile(
    depth=1,
    reliability=ReliabilityPolicy.RELIABLE,
    durability=DurabilityPolicy.TRANSIENT_LOCAL,
    history=HistoryPolicy.KEEP_LAST,
)

TF_TIMEOUT  = Duration(seconds=0.05)
OOM_TIMEOUT = Duration(seconds=0.10)


class PoseNormalizer(Node):
    def __init__(self) -> None:
        super().__init__('pose_normalizer')

        self.declare_parameter('robot_name', 'robot1')
        self._robot      = self.get_parameter('robot_name').value
        self._base_frame = f'{self._robot}/base_footprint'
        self._last_odom: Odometry | None = None

        self._tf_buffer   = tf2_ros.Buffer()
        self._tf_listener = tf2_ros.TransformListener(self._tf_buffer, self)

        # Subscribers — relative names resolve to /robotX/... inside namespace
        self.create_subscription(
            PoseWithCovarianceStamped, 'amcl_pose', self._amcl_cb, AMCL_QOS)
        self.create_subscription(
            Odometry, 'odom', self._odom_cb, 10)

        # Publishers — all in map frame, relative names inside namespace
        self._pub_position  = self.create_publisher(PoseStamped, 'position',  10)
        self._pub_tf_pose   = self.create_publisher(PoseStamped, 'tf_pose',   10)
        self._pub_odom_pose = self.create_publisher(PoseStamped, 'odom_pose', 10)

        self.create_timer(0.1, self._timer_cb)  # 10 Hz for TF-derived pose

        self.get_logger().info(
            f'[{self._robot}] pose_normalizer ready\n'
            f'  /{self._robot}/position   ← AMCL  (authoritative, map frame)\n'
            f'  /{self._robot}/tf_pose    ← TF lookup map→{self._base_frame}\n'
            f'  /{self._robot}/odom_pose  ← EKF odom projected into map'
        )

    # ── AMCL callback → /robotX/position ─────────────────────────────────────

    def _amcl_cb(self, msg: PoseWithCovarianceStamped) -> None:
        out = PoseStamped()
        out.header = msg.header   # frame_id = map, stamp from AMCL
        out.pose   = msg.pose.pose
        self._pub_position.publish(out)

    # ── EKF odom callback → /robotX/odom_pose ────────────────────────────────

    def _odom_cb(self, msg: Odometry) -> None:
        self._last_odom = msg
        # Project EKF odom pose (frame: robotX/odom) into map frame.
        # AMCL provides the map→robotX/odom transform; composing gives
        # base_footprint in map — the dead-reckoning view of global position.
        odom_in_odom = PoseStamped()
        odom_in_odom.header = msg.header   # frame_id = robotX/odom
        odom_in_odom.pose   = msg.pose.pose
        try:
            in_map = self._tf_buffer.transform(
                odom_in_odom, 'map', timeout=OOM_TIMEOUT)
            self._pub_odom_pose.publish(in_map)
        except (tf2_ros.LookupException, tf2_ros.ExtrapolationException,
                tf2_ros.ConnectivityException):
            pass  # suppress until AMCL warms up and TF is available

    # ── Timer → /robotX/tf_pose ───────────────────────────────────────────────

    def _timer_cb(self) -> None:
        # Direct TF lookup: map → robotX/base_footprint at latest available time.
        # This is the combined AMCL+EKF view and should closely track /position.
        try:
            t = self._tf_buffer.lookup_transform(
                'map', self._base_frame, Time(), timeout=TF_TIMEOUT)
        except (tf2_ros.LookupException, tf2_ros.ExtrapolationException,
                tf2_ros.ConnectivityException):
            return

        out = PoseStamped()
        out.header.stamp    = t.header.stamp
        out.header.frame_id = 'map'
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
