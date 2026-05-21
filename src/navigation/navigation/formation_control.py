#!/usr/bin/env python3
"""
formation_control.py
====================
APF-based aggregation for a fixed pair of robots.  Simpler and faster to
start than formation_control_3 when you only need two specific robots.

Configure the pair by editing the two lines in the USER CONFIG block below.
Both robots must have their /robotX/odom visible in this domain.

Usage:
  ros2 run navigation formation_control
"""

import math
import threading

import rclpy
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from std_msgs.msg import Bool


# ══════════════════════════════════════════════════════════════════════════
#  USER CONFIG — change only these lines to swap the robot pair
# ══════════════════════════════════════════════════════════════════════════
ROBOT_A = '/robot1'
ROBOT_B = '/robot2'
# ══════════════════════════════════════════════════════════════════════════

GOAL_TOLERANCE = 0.05   # m
LINEAR_SPEED   = 0.3    # m/s
G_A            = 10.0   # attraction gain
G_R            = 0.5    # repulsion gain

YAW_GAIN     = 1.0
YAW_MAX      = 0.5
YAW_DEADBAND = 0.05


# ── Helpers ───────────────────────────────────────────────────────────────────

def wrap_angle(a: float) -> float:
    return math.atan2(math.sin(a), math.cos(a))


def yaw_from_quat(q) -> float:
    return math.atan2(
        2.0 * (q.w * q.z + q.x * q.y),
        1.0 - 2.0 * (q.y * q.y + q.z * q.z),
    )


class Vec2:
    __slots__ = ('x', 'y')

    def __init__(self, x: float = 0.0, y: float = 0.0):
        self.x = x
        self.y = y

    def __neg__(self):        return Vec2(-self.x, -self.y)
    def __add__(self, o):     return Vec2(self.x + o.x, self.y + o.y)
    def __sub__(self, o):     return Vec2(self.x - o.x, self.y - o.y)
    def __mul__(self, s):     return Vec2(self.x * s,   self.y * s)
    def __truediv__(self, s): return Vec2(self.x / s,   self.y / s)

    def norm(self) -> float:
        return math.hypot(self.x, self.y)

    def normalized(self) -> 'Vec2':
        n = self.norm()
        return self / n if n > 1e-9 else Vec2()


# ── RobotDriver ───────────────────────────────────────────────────────────────

class RobotDriver(Node):
    def __init__(self, namespace: str, all_namespaces: list[str]):
        super().__init__(f'{namespace.strip("/")}_driver')

        self.namespace = namespace
        self.peer: 'RobotDriver | None' = None

        self._lock = threading.Lock()
        self._pos: Vec2 | None = None
        self.yaw: float | None = None
        self.start_yaw: float | None = None
        self.odom_ready = False

        self.ready_peers: set[str] = set()
        self.all_namespaces: set[str] = set(all_namespaces) - {namespace}
        self.all_ready = False
        self.done = False

        self.cmd_pub = self.create_publisher(
            Twist, f'{namespace}/controller/cmd_vel', 10)
        self.ready_pub = self.create_publisher(
            Bool, f'{namespace}/ready', 10)

        self.create_subscription(
            Odometry, f'{namespace}/odom', self._odom_cb, 10)

        for ns in all_namespaces:
            if ns != namespace:
                self.create_subscription(
                    Bool, f'{ns}/ready',
                    lambda msg, ns=ns: self._ready_cb(ns), 10)

        self.create_timer(0.05, self._control_loop)
        # Re-broadcast readiness at 5 Hz until all peers have confirmed.
        # A single publish inside _odom_cb would be silently lost if the
        # peer subscriber hasn't registered yet.
        self.create_timer(0.2, self._broadcast_ready)

        self.get_logger().info(f'[{namespace}] Driver ready.')

    def set_peer(self, peer: 'RobotDriver') -> None:
        self.peer = peer

    def get_position(self) -> 'Vec2 | None':
        with self._lock:
            return self._pos

    def _odom_cb(self, msg: Odometry) -> None:
        p = msg.pose.pose
        with self._lock:
            self._pos = Vec2(p.position.x, p.position.y)
        self.yaw = yaw_from_quat(p.orientation)
        self.odom_ready = True
        if self.start_yaw is None:
            self.start_yaw = self.yaw

    def _broadcast_ready(self) -> None:
        if self.odom_ready and not self.all_ready:
            self.ready_pub.publish(Bool(data=True))

    def _ready_cb(self, peer_ns: str) -> None:
        if self.all_ready:
            return
        self.ready_peers.add(peer_ns)
        if self.all_namespaces.issubset(self.ready_peers):
            self.all_ready = True
            self.get_logger().info(
                f'[{self.namespace}] All peers ready — starting.')

    def _control_loop(self) -> None:
        if self.done or not self.odom_ready or not self.all_ready:
            return
        if self.peer is None or not self.peer.odom_ready:
            return
        if self.start_yaw is None or self.yaw is None:
            return

        pos_self = self.get_position()
        pos_peer = self.peer.get_position()
        if pos_self is None or pos_peer is None:
            return

        delta = pos_self - pos_peer
        dist = delta.norm()

        if dist < GOAL_TOLERANCE:
            self.cmd_pub.publish(Twist())
            self.done = True
            self.get_logger().info(
                f'[{self.namespace}] Done! dist={dist:.3f} m '
                f'pos=({pos_self.x:.3f},{pos_self.y:.3f})')
            return

        direction = delta.normalized()
        f_attract = -direction * G_A * dist
        f_repulse =  direction * G_R / max(dist ** 2, 1e-6)
        f_total   = f_attract + f_repulse

        fn = f_total.norm()
        if fn < 1e-6:
            return

        wv = f_total / fn * LINEAR_SPEED

        c = math.cos(self.yaw)
        s = math.sin(self.yaw)
        lx =  c * wv.x + s * wv.y
        ly = -s * wv.x + c * wv.y

        mx = LINEAR_SPEED / math.sqrt(2)
        lx = max(-mx, min(mx, lx))
        ly = max(-mx, min(mx, ly))

        yaw_err = wrap_angle(self.yaw - self.start_yaw)
        wz = 0.0
        if abs(yaw_err) > YAW_DEADBAND:
            wz = max(-YAW_MAX, min(YAW_MAX, -YAW_GAIN * yaw_err))

        twist = Twist()
        twist.linear.x  = lx
        twist.linear.y  = ly
        twist.angular.z = wz
        self.cmd_pub.publish(twist)

        self.get_logger().info(
            f'[{self.namespace}] dist={dist:.3f} vx={lx:.3f} vy={ly:.3f}',
            throttle_duration_sec=0.5)


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    print(f'\nFormation control: {ROBOT_A} ↔ {ROBOT_B}\n')
    rclpy.init()

    namespaces = [ROBOT_A, ROBOT_B]
    robot_a = RobotDriver(ROBOT_A, namespaces)
    robot_b = RobotDriver(ROBOT_B, namespaces)
    robot_a.set_peer(robot_b)
    robot_b.set_peer(robot_a)

    executor = MultiThreadedExecutor(num_threads=4)
    executor.add_node(robot_a)
    executor.add_node(robot_b)

    last_log = 0.0

    try:
        while rclpy.ok():
            executor.spin_once(timeout_sec=0.05)

            pa = robot_a.get_position()
            pb = robot_b.get_position()
            now = robot_a.get_clock().now().nanoseconds * 1e-9

            if pa and pb and now - last_log >= 1.0:
                dist = (pa - pb).norm()
                print(f'[status]  {ROBOT_A}=({pa.x:.3f},{pa.y:.3f})  '
                      f'{ROBOT_B}=({pb.x:.3f},{pb.y:.3f})  |Δ|={dist:.3f}m')
                last_log = now

            if robot_a.done and robot_b.done:
                pa = robot_a.get_position()
                pb = robot_b.get_position()
                dist = (pa - pb).norm() if pa and pb else float('nan')
                print(f'\nDone.\n'
                      f'  {ROBOT_A}: ({pa.x:.3f},{pa.y:.3f})\n'
                      f'  {ROBOT_B}: ({pb.x:.3f},{pb.y:.3f})\n'
                      f'  Final dist: {dist:.3f} m')
                break

    except KeyboardInterrupt:
        print('\nInterrupted.')
    finally:
        stop = Twist()
        robot_a.cmd_pub.publish(stop)
        robot_b.cmd_pub.publish(stop)
        robot_a.destroy_node()
        robot_b.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
