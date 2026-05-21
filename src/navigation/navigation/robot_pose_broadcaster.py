#!/usr/bin/env python3
"""
robot_pose_broadcaster.py
=========================
Simulates one robot's presence on the shared ROS graph without hardware.

Publishes:
  /robotX/odom  (nav_msgs/Odometry, 10 Hz, frame_id=robotX/odom)

Broadcasts TF:
  robotX/odom → robotX/base_footprint  (dynamic, 10 Hz)
  robotX/base_footprint → robotX/lidar_frame  (static, z offset)

Subscribes:
  /robotX/initialpose  (PoseWithCovarianceStamped)
    RViz "2D Pose Estimate" button updates the robot position in real time.
    In RViz Tool Properties, set the topic to /robot2/initialpose etc.

Parameters
----------
robot_name     str    e.g. 'robot2'
x              float  initial x in odom frame (m)
y              float  initial y in odom frame (m)
yaw            float  initial yaw in odom frame (rad)
lidar_z_offset float  height of lidar above base_footprint (m)
wander         bool   move in a circle if true
wander_radius  float  radius of wander circle (m)
wander_speed   float  angular speed around circle (rad/s)
"""

import math
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, DurabilityPolicy, ReliabilityPolicy, HistoryPolicy
import tf2_ros
from geometry_msgs.msg import PoseWithCovarianceStamped, TransformStamped
from nav_msgs.msg import Odometry


ODOM_QOS = QoSProfile(
    depth=1,
    reliability=ReliabilityPolicy.RELIABLE,
    durability=DurabilityPolicy.VOLATILE,
    history=HistoryPolicy.KEEP_LAST,
)


def _yaw_to_quat(yaw: float):
    h = yaw * 0.5
    return 0.0, 0.0, math.sin(h), math.cos(h)


class RobotPoseBroadcaster(Node):
    def __init__(self):
        super().__init__('robot_pose_broadcaster')

        self.declare_parameter('robot_name',     'robot1')
        self.declare_parameter('x',              0.0)
        self.declare_parameter('y',              0.0)
        self.declare_parameter('yaw',            0.0)
        self.declare_parameter('lidar_z_offset', 0.10)
        self.declare_parameter('wander',         False)
        self.declare_parameter('wander_radius',  1.0)
        self.declare_parameter('wander_speed',   0.3)

        self._robot  = self.get_parameter('robot_name').value
        self._x      = float(self.get_parameter('x').value)
        self._y      = float(self.get_parameter('y').value)
        self._yaw    = float(self.get_parameter('yaw').value)
        lidar_z      = float(self.get_parameter('lidar_z_offset').value)
        self._wander = bool(self.get_parameter('wander').value)
        self._w_r    = float(self.get_parameter('wander_radius').value)
        self._w_spd  = float(self.get_parameter('wander_speed').value)

        self._w_cx  = self._x
        self._w_cy  = self._y
        self._w_ang = 0.0

        self._odom_frame = f'{self._robot}/odom'
        self._base_frame = f'{self._robot}/base_footprint'

        self._tf_dyn    = tf2_ros.TransformBroadcaster(self)
        self._tf_static = tf2_ros.StaticTransformBroadcaster(self)

        self._odom_pub = self.create_publisher(
            Odometry, f'/{self._robot}/odom', ODOM_QOS)

        self.create_subscription(
            PoseWithCovarianceStamped,
            f'/{self._robot}/initialpose',
            self._initialpose_cb,
            10,
        )

        self._send_static(self._base_frame, f'{self._robot}/lidar_frame',
                          0.0, 0.0, lidar_z, 0.0)

        self.create_timer(0.1, self._step)

        self.get_logger().info(
            f'[{self._robot}] broadcaster ready  '
            f'x={self._x:.2f} y={self._y:.2f} yaw={math.degrees(self._yaw):.1f}°  '
            f'wander={self._wander}'
        )

    def _initialpose_cb(self, msg: PoseWithCovarianceStamped) -> None:
        p = msg.pose.pose
        self._x = p.position.x
        self._y = p.position.y
        z, w = p.orientation.z, p.orientation.w
        self._yaw = 2.0 * math.atan2(z, w)
        self._w_cx = self._x
        self._w_cy = self._y
        self._w_ang = 0.0
        self.get_logger().info(
            f'[{self._robot}] pose updated → '
            f'x={self._x:.3f} y={self._y:.3f} yaw={math.degrees(self._yaw):.1f}°'
        )

    def _step(self) -> None:
        if self._wander:
            dt = 0.1
            self._w_ang += self._w_spd * dt
            self._x = self._w_cx + self._w_r * math.cos(self._w_ang)
            self._y = self._w_cy + self._w_r * math.sin(self._w_ang)
            self._yaw = self._w_ang + math.pi * 0.5

        now = self.get_clock().now().to_msg()
        qx, qy, qz, qw = _yaw_to_quat(self._yaw)

        t = TransformStamped()
        t.header.stamp    = now
        t.header.frame_id = self._odom_frame
        t.child_frame_id  = self._base_frame
        t.transform.translation.x = self._x
        t.transform.translation.y = self._y
        t.transform.translation.z = 0.0
        t.transform.rotation.x = qx
        t.transform.rotation.y = qy
        t.transform.rotation.z = qz
        t.transform.rotation.w = qw
        self._tf_dyn.sendTransform(t)

        self._publish_odom(now, qx, qy, qz, qw)

    def _make_tf(self, parent, child, x, y, z, yaw) -> TransformStamped:
        t = TransformStamped()
        t.header.stamp    = self.get_clock().now().to_msg()
        t.header.frame_id = parent
        t.child_frame_id  = child
        t.transform.translation.x = x
        t.transform.translation.y = y
        t.transform.translation.z = z
        qx, qy, qz, qw = _yaw_to_quat(yaw)
        t.transform.rotation.x = qx
        t.transform.rotation.y = qy
        t.transform.rotation.z = qz
        t.transform.rotation.w = qw
        return t

    def _send_static(self, parent, child, x, y, z, yaw) -> None:
        self._tf_static.sendTransform(self._make_tf(parent, child, x, y, z, yaw))

    def _publish_odom(self, stamp, qx, qy, qz, qw) -> None:
        msg = Odometry()
        msg.header.stamp    = stamp
        msg.header.frame_id = self._odom_frame
        msg.child_frame_id  = self._base_frame
        msg.pose.pose.position.x = self._x
        msg.pose.pose.position.y = self._y
        msg.pose.pose.orientation.x = qx
        msg.pose.pose.orientation.y = qy
        msg.pose.pose.orientation.z = qz
        msg.pose.pose.orientation.w = qw
        msg.pose.covariance[0]  = 0.01
        msg.pose.covariance[7]  = 0.01
        msg.pose.covariance[35] = 0.01
        self._odom_pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = RobotPoseBroadcaster()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
