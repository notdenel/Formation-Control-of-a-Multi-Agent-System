#!/usr/bin/env python3
"""
Aggregate any three robots together using APF + odometry feedback.
Robots use mecanum wheels and strafe without changing heading.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  TO CONFIGURE FOR A DIFFERENT ROBOT TRIO:
  Only edit the three lines inside the "USER CONFIG" block below.
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
#  USER CONFIG  ── only change these three lines to swap robot trios
# ══════════════════════════════════════════════════════════════════════════════
ROBOT_A = '/robot1'
ROBOT_B = '/robot3'
ROBOT_C = '/robot5'
# ══════════════════════════════════════════════════════════════════════════════


LINEAR_SPEED   = 5.0   # m/s  – max speed along dominant axis
GOAL_TOLERANCE = (0.5 / 10.0) ** (1/3)  # natural APF equilibrium ≈ 0.368 m

# APF gains
G_A = 10.0  # attraction gain
G_R = 0.5   # repulsion gain

#Inter-agent distances
DIST_12 = 1.0
DIST_13 = 1.0
DIST_23 = 1.0

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
    Sums APF forces over ALL peers: J_i(x) = Σ_{j≠i} [J_a(||xi-xj||) - J_r(||xi-xj||)]
    Thread-safe: peer positions are accessed under locks.
    """

    def __init__(self, namespace: str, all_namespaces: list[str]):
        super().__init__(f'{namespace.strip("/")}_driver')

        self.namespace = namespace
        self.peers: list['RobotDriver'] = []   # set via add_peer()

        # ── thread-safe position ──────────────────────────────────────────────
        self._pos_lock = threading.Lock()
        self._pos: Vec2 | None = None

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

    def add_peer(self, peer: 'RobotDriver') -> None:
        self.peers.append(peer)

    def get_position(self) -> 'Vec2 | None':
        """Thread-safe position read."""
        with self._pos_lock:
            return self._pos

    # ── ROS callbacks ─────────────────────────────────────────────────────────

    def _odom_cb(self, msg: Odometry) -> None:
        pose = msg.pose.pose

        with self._pos_lock:
            self._pos = Vec2(pose.position.x, pose.position.y)

        self.current_yaw = yaw_from_quaternion(pose.orientation)
        self.odom_ready  = True

        if self.start_yaw is None:
            self.start_yaw = self.current_yaw

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
        if not all(p.odom_ready for p in self.peers):
            return
        if self.start_yaw is None:
            return

        pos_self = self.get_position()
        if pos_self is None:
            return

        # ── J_i(x) = Σ_{j≠i} [ J_a(||xi-xj||) - J_r(||xi-xj||) ] ──────────
        f_total   = Vec2()
        distances = []

        for peer in self.peers:
            pos_peer = peer.get_position()
            if pos_peer is None:
                return

            delta    = pos_self - pos_peer   # vector: peer → self
            distance = delta.norm()
            distances.append(distance)

            if distance < 1e-6:              # avoid division by zero
                continue

            direction = delta.normalized()

            # Negative gradient of J_a = ½·G_A·d²  →  -G_A·d (toward peer)
            f_attract = -direction * G_A * distance

            # Negative gradient of J_r = ½·G_R/d²  →  +G_R/d² (away from peer)
            f_repulse =  direction * G_R / (distance ** 2)

            f_total = f_total + f_attract + f_repulse

        # ── Goal check — ALL pairwise distances below tolerance ───────────────
        if all(d < GOAL_TOLERANCE for d in distances):
            self.cmd_pub.publish(Twist())
            self.done = True
            self.get_logger().info(
                f'[{self.namespace}] Aggregation complete! '
                f'dists={[f"{d:.3f}" for d in distances]}  '
                f'pos=({pos_self.x:.3f}, {pos_self.y:.3f})')
            return

        # ── World → body-frame transform ──────────────────────────────────────
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

        # ── Publish ───────────────────────────────────────────────────────────
        twist = Twist()
        twist.linear.x  = local_x
        twist.linear.y  = local_y
        twist.angular.z = wz
        self.cmd_pub.publish(twist)

        self.get_logger().info(
            f'[{self.namespace}] dists={[f"{d:.3f}" for d in distances]}  '
            f'vx={local_x:.3f}  vy={local_y:.3f}',
            throttle_duration_sec=0.5)


# ── Utility ───────────────────────────────────────────────────────────────────

def all_pairwise_distances(robots: list[RobotDriver]) -> list[float] | None:
    results = []
    for i, a in enumerate(robots):
        for b in robots[i+1:]:
            pa, pb = a.get_position(), b.get_position()
            if pa is None or pb is None:
                return None
            results.append((pa - pb).norm())
    return results


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    print(f'\nStarting aggregation: {ROBOT_A} ↔ {ROBOT_B} ↔ {ROBOT_C}\n')

    rclpy.init()

    namespaces = [ROBOT_A, ROBOT_B, ROBOT_C]
    robot_a    = RobotDriver(ROBOT_A, namespaces)
    robot_b    = RobotDriver(ROBOT_B, namespaces)
    robot_c    = RobotDriver(ROBOT_C, namespaces)

    # Each robot tracks all others as peers (implements the Σ_{j≠i} sum)
    robot_a.add_peer(robot_b); robot_a.add_peer(robot_c)
    robot_b.add_peer(robot_a); robot_b.add_peer(robot_c)
    robot_c.add_peer(robot_a); robot_c.add_peer(robot_b)

    executor = MultiThreadedExecutor(num_threads=6)
    executor.add_node(robot_a)
    executor.add_node(robot_b)
    executor.add_node(robot_c)

    robots   = [robot_a, robot_b, robot_c]
    last_log = 0.0

    try:
        while rclpy.ok():
            executor.spin_once(timeout_sec=0.05)

            dists = all_pairwise_distances(robots)
            now   = robot_a.get_clock().now().nanoseconds * 1e-9

            if dists is not None and (now - last_log) >= 1.0:
                positions = [r.get_position() for r in robots]
                print(
                    f'[status]  '
                    f'{ROBOT_A}=({positions[0].x:.3f}, {positions[0].y:.3f})  '
                    f'{ROBOT_B}=({positions[1].x:.3f}, {positions[1].y:.3f})  '
                    f'{ROBOT_C}=({positions[2].x:.3f}, {positions[2].y:.3f})  '
                    f'|Δ|={[f"{d:.3f}" for d in dists]}'
                )
                last_log = now

            if all(r.done for r in robots):
                positions = [r.get_position() for r in robots]
                dists     = all_pairwise_distances(robots)
                print(
                    f'\nAll robots aggregated.\n'
                    f'  {ROBOT_A} final: ({positions[0].x:.3f}, {positions[0].y:.3f})\n'
                    f'  {ROBOT_B} final: ({positions[1].x:.3f}, {positions[1].y:.3f})\n'
                    f'  {ROBOT_C} final: ({positions[2].x:.3f}, {positions[2].y:.3f})\n'
                    f'  Final pairwise distances: {[f"{d:.3f}" for d in dists]}'
                )
                break

    except KeyboardInterrupt:
        print('\nInterrupted by user.')
    finally:
        stop = Twist()
        for r in robots:
            r.cmd_pub.publish(stop)
            r.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()