#!/usr/bin/env python3
"""
Aggregate any two robots together using APF + odometry feedback.
Robots use mecanum wheels and strafe without changing heading.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  TO CONFIGURE FOR A DIFFERENT ROBOT PAIR:
  Only edit the two lines inside the "USER CONFIG" block below.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Usage:
    ros2 run navigation formation_control
"""

import threading
import math

import rclpy
from rclpy.node import Node
from rclpy.executors import MultiThreadedExecutor
from nav_msgs.msg import Odometry
from geometry_msgs.msg import Twist
from std_msgs.msg import Bool


# ══════════════════════════════════════════════════════════════════════════════
#  USER CONFIG  ── only change these two lines to swap robot pairs
# ══════════════════════════════════════════════════════════════════════════════
ROBOT_A = '/robot1'
ROBOT_B = '/robot3'
# ══════════════════════════════════════════════════════════════════════════════


LINEAR_SPEED   = 5.0   # m/s  – max speed along dominant axis
GOAL_TOLERANCE = 0.05  # m    – stop when inter-robot distance is this small

# APF gains
G_A = 10.0   # attraction gain  (toward peer)
G_R = 0.5   # repulsion gain   (away from peer at close range)

# Yaw-drift correction
YAW_CORRECTION_GAIN       = 1.0   # rad/s per rad
YAW_CORRECTION_MAX_RAD_S  = 0.5   # clamp (rad/s)
YAW_CORRECTION_THRESH_RAD = 0.05  # deadband (~3°)


# ── Helpers ───────────────────────────────────────────────────────────────────

def wrap_angle(angle: float) -> float:
    return math.atan2(math.sin(angle), math.cos(angle))


class Vec2:
    """Minimal 2-D vector."""

    def __init__(self, x: float = 0.0, y: float = 0.0):
        self.x = x
        self.y = y

    def __neg__(self)           -> 'Vec2': return Vec2(-self.x, -self.y)
    def __add__(self, o)        -> 'Vec2': return Vec2(self.x + o.x, self.y + o.y)
    def __sub__(self, o)        -> 'Vec2': return Vec2(self.x - o.x, self.y - o.y)
    def __mul__(self, s: float) -> 'Vec2': return Vec2(self.x * s,   self.y * s)
    def __rmul__(self, s)       -> 'Vec2': return self.__mul__(s)
    def __truediv__(self, s)    -> 'Vec2': return Vec2(self.x / s,   self.y / s)
    def __repr__(self)          -> str:    return f'Vec2({self.x:.3f}, {self.y:.3f})'

    def norm(self) -> float:
        return math.hypot(self.x, self.y)

    def normalized(self) -> 'Vec2':
        n = self.norm()
        return self / n if n > 1e-9 else Vec2()


def yaw_from_quaternion(q) -> float:
    siny_cosp = 2.0 * (q.w * q.z + q.x * q.y)
    cosy_cosp = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
    return math.atan2(siny_cosp, cosy_cosp)


# ── RobotDriver ───────────────────────────────────────────────────────────────

class RobotDriver(Node):
    """
    Controls one robot namespace.
    Thread-safe: peer position is accessed under a lock so the
    MultiThreadedExecutor cannot produce torn reads.
    """

    def __init__(self, namespace: str, all_namespaces: list[str]):
        super().__init__(f'{namespace.strip("/")}_driver')

        self.namespace = namespace
        self.peer: 'RobotDriver | None' = None

        # ── thread-safe position ──────────────────────────────────────────────
        self._pos_lock = threading.Lock()
        self._pos: Vec2 | None = None          # always written under lock

        self.current_yaw: float | None = None
        self.start_yaw:   float | None = None
        self.odom_ready   = False

        # ── peer-ready handshake ──────────────────────────────────────────────
        self.ready_peers    = set()
        self.all_namespaces = set(all_namespaces) - {namespace}
        self.all_ready      = False
        self.done           = False

        # ── ROS I/O ───────────────────────────────────────────────────────────
        self.cmd_pub   = self.create_publisher(Twist, f'{namespace}/cmd_vel', 10)
        self.ready_pub = self.create_publisher(Bool,  f'{namespace}/ready',   10)

        self.create_subscription(
            Odometry, f'{namespace}/odom', self._odom_cb, 10)

        for ns in all_namespaces:
            if ns != namespace:
                self.create_subscription(
                    Bool, f'{ns}/ready',
                    lambda msg, ns=ns: self._ready_cb(ns),
                    10)

        self.create_timer(0.05, self._control_loop)
        self.get_logger().info(f'[{namespace}] Driver initialised.')

    # ── public API ────────────────────────────────────────────────────────────

    def set_peer(self, peer: 'RobotDriver') -> None:
        self.peer = peer

    def get_position(self) -> 'Vec2 | None':
        """Thread-safe position read."""
        with self._pos_lock:
            return self._pos

    # ── ROS callbacks ─────────────────────────────────────────────────────────

    def _odom_cb(self, msg: Odometry) -> None:
        pose = msg.pose.pose

        # Atomic position update — prevents torn reads in the control loop
        with self._pos_lock:
            self._pos = Vec2(pose.position.x, pose.position.y)

        self.current_yaw = yaw_from_quaternion(pose.orientation)
        self.odom_ready  = True

        if self.start_yaw is None:
            self.start_yaw = self.current_yaw

        # Stop advertising readiness once everyone is synchronised
        if not self.all_ready:
            self.ready_pub.publish(Bool(data=True))

    def _ready_cb(self, peer_ns: str) -> None:
        if self.all_ready:
            return

        self.ready_peers.add(peer_ns)

        if self.all_namespaces.issubset(self.ready_peers):
            self.all_ready = True
            self.get_logger().info(
                f'[{self.namespace}] All peers ready — starting aggregation!')

    # ── Control loop ──────────────────────────────────────────────────────────

    def _control_loop(self) -> None:
        if self.done or not self.odom_ready or not self.all_ready:
            return
        if self.peer is None or not self.peer.odom_ready:
            return
        if self.start_yaw is None:
            return

        # Thread-safe reads for both positions
        pos_self = self.get_position()
        pos_peer = self.peer.get_position()

        if pos_self is None or pos_peer is None:
            return

        delta    = pos_self - pos_peer   # vector pointing from peer → self
        distance = delta.norm()

        # ── Goal check ────────────────────────────────────────────────────────
        if distance < GOAL_TOLERANCE:
            self.cmd_pub.publish(Twist())           # full stop
            self.done = True
            self.get_logger().info(
                f'[{self.namespace}] Aggregation complete! '
                f'dist={distance:.3f} m  '
                f'pos=({pos_self.x:.3f}, {pos_self.y:.3f})')
            return

        # ── APF forces (world frame) ──────────────────────────────────────────
        
        direction = delta.normalized()          # unit vector: peer → self

        # Attraction: pulls self toward peer (negative gradient of ½·G_A·d²)
        f_attract = -direction * G_A * distance

        # Repulsion: pushes self away from peer (negative gradient of ½·G_R/d²)
        f_repulse =  direction * G_R / (distance ** 2)

        f_total = f_attract + f_repulse

        # ── World → body-frame transform ─────────────────────────────────────
        c = math.cos(self.current_yaw)
        s = math.sin(self.current_yaw)

        local_x =  c * f_total.x + s * f_total.y
        local_y = -s * f_total.x + c * f_total.y

        # ── Yaw-drift correction ──────────────────────────────────────────────
        yaw_error = wrap_angle(self.current_yaw - self.start_yaw)
        wz = 0.0
        if abs(yaw_error) > YAW_CORRECTION_THRESH_RAD:
            wz = max(
                -YAW_CORRECTION_MAX_RAD_S,
                min(YAW_CORRECTION_MAX_RAD_S, -YAW_CORRECTION_GAIN * yaw_error),
            )
            self.get_logger().debug(
                f'[{self.namespace}] yaw_err={math.degrees(yaw_error):.1f}°  '
                f'wz={wz:.3f} rad/s',
                throttle_duration_sec=1.0)

        # ── Publish ───────────────────────────────────────────────────────────
        twist = Twist()
        twist.linear.x  = local_x
        twist.linear.y  = local_y
        twist.angular.z = wz
        self.cmd_pub.publish(twist)

        self.get_logger().info(
            f'[{self.namespace}] dist={distance:.3f} m  '
            f'vx={local_x:.3f}  vy={local_y:.3f}',
            throttle_duration_sec=0.5)


# ── Utility ───────────────────────────────────────────────────────────────────

def inter_robot_distance(a: RobotDriver, b: RobotDriver) -> float | None:
    pa, pb = a.get_position(), b.get_position()
    if pa is None or pb is None:
        return None
    return (pa - pb).norm()


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    print(f'\nStarting aggregation: {ROBOT_A} ↔ {ROBOT_B}\n')

    rclpy.init()

    namespaces = [ROBOT_A, ROBOT_B]
    robot_a    = RobotDriver(ROBOT_A, namespaces)
    robot_b    = RobotDriver(ROBOT_B, namespaces)

    robot_a.set_peer(robot_b)
    robot_b.set_peer(robot_a)

    executor = MultiThreadedExecutor(num_threads=4)
    executor.add_node(robot_a)
    executor.add_node(robot_b)

    last_log = 0.0

    try:
        while rclpy.ok():
            executor.spin_once(timeout_sec=0.05)

            dist = inter_robot_distance(robot_a, robot_b)
            now  = robot_a.get_clock().now().nanoseconds * 1e-9

            if dist is not None and (now - last_log) >= 1.0:
                pa, pb = robot_a.get_position(), robot_b.get_position()
                print(
                    f'[status]  '
                    f'{ROBOT_A}=({pa.x:.3f}, {pa.y:.3f})  '
                    f'{ROBOT_B}=({pb.x:.3f}, {pb.y:.3f})  '
                    f'|Δ|={dist:.3f} m'
                )
                last_log = now

            if robot_a.done and robot_b.done:
                pa, pb = robot_a.get_position(), robot_b.get_position()
                print(
                    f'\nBoth robots aggregated.\n'
                    f'  {ROBOT_A} final: ({pa.x:.3f}, {pa.y:.3f})\n'
                    f'  {ROBOT_B} final: ({pb.x:.3f}, {pb.y:.3f})\n'
                    f'  Final inter-agent distance: '
                    f'{inter_robot_distance(robot_a, robot_b):.3f} m'
                )
                break

    except KeyboardInterrupt:
        print('\nInterrupted by user.')
    finally:
        stop = Twist()
        robot_a.cmd_pub.publish(stop)
        robot_b.cmd_pub.publish(stop)
        robot_a.destroy_node()
        robot_b.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()