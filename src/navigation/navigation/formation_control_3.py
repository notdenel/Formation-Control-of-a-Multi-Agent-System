#!/usr/bin/env python3
"""
Multi-robot formation control using APF + joystick-controlled centroid.
Robots discover each other automatically from active /robotX/odom topics.
Centroid starts at (0,0) and is moved by integrating /controller/cmd_vel.

Usage:
    ros2 run navigation aggregation
"""

import threading
import math
import re

import rclpy
from rclpy.node import Node
from rclpy.executors import MultiThreadedExecutor
from nav_msgs.msg import Odometry
from geometry_msgs.msg import Twist
from std_msgs.msg import Bool


# ── APF gains ─────────────────────────────────────────────────────────────────
G_A            = 10.0
G_R            = 0.5
G_TRACK        = 1.0
GOAL_TOLERANCE = 0.05   # m
LINEAR_SPEED   = 1.0    # m/s

# ── Desired inter-agent distances (metres) ────────────────────────────────────
# Row/col order matches sorted discovery order e.g. [/robot1, /robot3, /robot5]
#             robot1  robot3  robot5
DIST_MATRIX = [
    [0.0,    1.0,    1.5],
    [1.0,    0.0,    1.0],
    [1.5,    1.0,    0.0],
]

# Yaw-drift correction
YAW_CORRECTION_GAIN       = 1.0
YAW_CORRECTION_MAX_RAD_S  = 0.5
YAW_CORRECTION_THRESH_RAD = 0.05

DT = 0.05   # control loop period (s) — matches create_timer interval


# ── Helpers ───────────────────────────────────────────────────────────────────

def wrap_angle(a: float) -> float:
    return math.atan2(math.sin(a), math.cos(a))


class Vec2:
    __slots__ = ('x', 'y')

    def __init__(self, x: float = 0.0, y: float = 0.0):
        self.x = x; self.y = y

    def __add__(self, o):  return Vec2(self.x + o.x, self.y + o.y)
    def __sub__(self, o):  return Vec2(self.x - o.x, self.y - o.y)
    def __mul__(self, s):  return Vec2(self.x * s,   self.y * s)
    def __rmul__(self, s): return self.__mul__(s)
    def __truediv__(self, s): return Vec2(self.x / s, self.y / s)

    def norm(self):
        return math.hypot(self.x, self.y)

    def normalized(self):
        n = self.norm()
        return Vec2(self.x / n, self.y / n) if n > 1e-9 else Vec2()


def yaw_from_quaternion(q) -> float:
    return math.atan2(
        2.0 * (q.w * q.z + q.x * q.y),
        1.0 - 2.0 * (q.y * q.y + q.z * q.z))


# ── DiscoveryNode ─────────────────────────────────────────────────────────────
#discovers nodes 
class DiscoveryNode(Node):
    ODOM_PATTERN = re.compile(r'^(/robot\w+)/odom$')

    def __init__(self):
        super().__init__('aggregation_discovery')

    def discover(self, timeout_sec: float = 5.0) -> list[str]:
        deadline = self.get_clock().now().nanoseconds * 1e-9 + timeout_sec
        found = []
        while self.get_clock().now().nanoseconds * 1e-9 < deadline:
            found = [
                m.group(1)
                for topic, _ in self.get_topic_names_and_types()
                if (m := self.ODOM_PATTERN.match(topic))
            ]
            if len(found) >= 2:
                break
            rclpy.spin_once(self, timeout_sec=0.2)
        self.get_logger().info(f'[discovery] Found: {sorted(found)}')
        return sorted(found)


# ── RobotDriver ───────────────────────────────────────────────────────────────

class RobotDriver(Node):
    """
    Controls one robot.

    Centroid starts at (0,0) and is integrated from /controller/cmd_vel
    by whichever driver instance receives it — all drivers share the same
    centroid object via a reference passed in at construction.
    """

    def __init__(
        self,
        namespace:      str,
        all_namespaces: list[str],
        centroid:       Vec2,
        centroid_lock:  threading.Lock,
    ):
        super().__init__(f'{namespace.strip("/")}_driver')

        self.namespace     = namespace
        self.centroid      = centroid       # shared mutable Vec2
        self.centroid_lock = centroid_lock

        self.peers:         list['RobotDriver'] = []
        self.desired_dists: list[float]         = []

        self._pos_lock = threading.Lock()
        self._pos: Vec2 | None = None
        self.current_yaw: float | None = None
        self.start_yaw:   float | None = None
        self.odom_ready   = False

        self.ready_peers    = set()
        self.all_namespaces = set(all_namespaces) - {namespace}
        self.all_ready      = False
        self.done           = False

        self.cmd_pub   = self.create_publisher(Twist, f'{namespace}/cmd_vel', 10)
        self.ready_pub = self.create_publisher(Bool,  f'{namespace}/ready',   10)

        self.create_subscription(Odometry, f'{namespace}/odom', self._odom_cb, 10)

        # Only one driver needs to subscribe to the joystick — but subscribing
        # from all is harmless and avoids picking a "primary" driver arbitrarily.
        # The centroid update is idempotent under the lock so duplicate callbacks
        # simply overwrite with the same value.
        self.create_subscription(Twist, '/controller/cmd_vel', self._joy_cb, 10)

        for ns in all_namespaces:
            if ns != namespace:
                self.create_subscription(
                    Bool, f'{ns}/ready',
                    lambda msg, ns=ns: self._ready_cb(ns), 10)

        self.create_timer(DT, self._control_loop)
        self.get_logger().info(f'[{namespace}] Driver initialised.')

    def add_peer(self, peer: 'RobotDriver', desired_dist: float) -> None:
        self.peers.append(peer)
        self.desired_dists.append(desired_dist)

    def get_position(self) -> 'Vec2 | None':
        with self._pos_lock:
            return self._pos

    # ── callbacks ─────────────────────────────────────────────────────────────

    def _odom_cb(self, msg: Odometry) -> None:
        p = msg.pose.pose
        with self._pos_lock:
            self._pos = Vec2(p.position.x, p.position.y)
        self.current_yaw = yaw_from_quaternion(p.orientation)
        self.odom_ready  = True
        if self.start_yaw is None:
            self.start_yaw = self.current_yaw
        if not self.all_ready:
            self.ready_pub.publish(Bool(data=True))

    def _joy_cb(self, msg: Twist) -> None:
        # Integrate joystick velocity into centroid position.
        # linear.x → centroid world-X,  linear.y → centroid world-Y.
        # All driver instances share the same centroid object; the lock
        # prevents torn writes when multiple callbacks fire concurrently.
        with self.centroid_lock:
            self.centroid.x += msg.linear.x * DT
            self.centroid.y += msg.linear.y * DT

    def _ready_cb(self, peer_ns: str) -> None:
        if self.all_ready:
            return
        self.ready_peers.add(peer_ns)
        if self.all_namespaces.issubset(self.ready_peers):
            self.all_ready = True
            self.get_logger().info(f'[{self.namespace}] All peers ready — starting!')

    # ── control loop ──────────────────────────────────────────────────────────

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

        # Snapshot all peer positions once to avoid torn reads mid-loop
        peer_positions: list[Vec2] = []
        for peer in self.peers:
            pp = peer.get_position()
            if pp is None:
                return
            peer_positions.append(pp)

        # Snapshot centroid
        with self.centroid_lock:
            cx, cy = self.centroid.x, self.centroid.y

        # ── Centroid tracking: G_TRACK * (centroid - xi) ──────────────────────
        f = Vec2(
            G_TRACK * (cx - pos_self.x),
            G_TRACK * (cy - pos_self.y),
        )

        # ── Pairwise APF: Σ_{j≠i} [ J_a - J_r ] * unit(xi - xj) ─────────────
        errors = []
        for pos_peer, d_star in zip(peer_positions, self.desired_dists):
            dx   = pos_self.x - pos_peer.x
            dy   = pos_self.y - pos_peer.y
            dist = math.hypot(dx, dy)

            if dist < 1e-6:
                errors.append(0.0)
                continue

            error = dist - d_star          # + too far, - too close
            errors.append(abs(error))

            if abs(error) < 1e-9:
                continue

            ux = dx / dist
            uy = dy / dist

            # Attraction toward desired distance; repulsion only when too close
            fa = -G_A * error
            fr =  G_R / (error ** 2) if error < 0 else 0.0

            f.x += ux * (fa + fr)
            f.y += uy * (fa + fr)

        # ── Goal check ────────────────────────────────────────────────────────
        if all(e < GOAL_TOLERANCE for e in errors):
            self.cmd_pub.publish(Twist())
            self.done = True
            self.get_logger().info(
                f'[{self.namespace}] Formation reached! '
                f'errors={[f"{e:.3f}" for e in errors]} m')
            return

        # ── Normalise → unit direction, scale to LINEAR_SPEED ─────────────────
        fn = math.hypot(f.x, f.y)
        if fn < 1e-6:
            return

        wx = f.x / fn * LINEAR_SPEED
        wy = f.y / fn * LINEAR_SPEED

        # ── World → body frame ────────────────────────────────────────────────
        c = math.cos(self.current_yaw)
        s = math.sin(self.current_yaw)
        lx =  c * wx + s * wy
        ly = -s * wx + c * wy

        # ── Per-axis clamp — equalises mecanum FR/BL wheel load ───────────────
        mx = LINEAR_SPEED / math.sqrt(2)
        lx = max(-mx, min(mx, lx))
        ly = max(-mx, min(mx, ly))

        # ── Yaw-drift correction ──────────────────────────────────────────────
        yaw_err = wrap_angle(self.current_yaw - self.start_yaw)
        wz = 0.0
        if abs(yaw_err) > YAW_CORRECTION_THRESH_RAD:
            wz = max(-YAW_CORRECTION_MAX_RAD_S,
                     min(YAW_CORRECTION_MAX_RAD_S, -YAW_CORRECTION_GAIN * yaw_err))

        twist = Twist()
        twist.linear.x  = lx
        twist.linear.y  = ly
        twist.angular.z = wz
        self.cmd_pub.publish(twist)

        self.get_logger().info(
            f'[{self.namespace}] errors={[f"{e:.3f}" for e in errors]}  '
            f'centroid=({cx:.2f},{cy:.2f})  vx={lx:.3f}  vy={ly:.3f}',
            throttle_duration_sec=0.5)


# ── Utility ───────────────────────────────────────────────────────────────────

def all_pairwise_errors(
        namespaces:  list[str],
        driver_map:  dict[str, RobotDriver],
        dist_matrix: list[list[float]],
) -> 'list[tuple] | None':
    out = []
    for i, a in enumerate(namespaces):
        for j, b in enumerate(namespaces):
            if j <= i:
                continue
            pa = driver_map[a].get_position()
            pb = driver_map[b].get_position()
            if pa is None or pb is None:
                return None
            out.append((a, b, math.hypot(pa.x - pb.x, pa.y - pb.y), dist_matrix[i][j]))
    return out


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    rclpy.init()

    discovery  = DiscoveryNode()
    namespaces = discovery.discover(timeout_sec=5.0)
    discovery.destroy_node()

    if len(namespaces) < 2:
        print(f'[aggregation] Need ≥2 robots, found {len(namespaces)}. Aborting.')
        rclpy.shutdown()
        return

    n = len(namespaces)

    if len(DIST_MATRIX) < n or any(len(r) < n for r in DIST_MATRIX):
        print(f'[aggregation] DIST_MATRIX too small for {n} robots. Aborting.')
        rclpy.shutdown()
        return

    print(f'\nFormation control: {" ↔ ".join(namespaces)}')
    print('Desired distances:')
    for i, a in enumerate(namespaces):
        for j, b in enumerate(namespaces):
            if j <= i:
                continue
            print(f'  {a} ↔ {b}: {DIST_MATRIX[i][j]:.3f} m')
    print(f'Centroid: (0.00, 0.00) — move with joystick on /controller/cmd_vel\n')

    # Shared centroid — all drivers hold a reference to the same object
    centroid      = Vec2(0.0, 0.0)
    centroid_lock = threading.Lock()

    driver_map: dict[str, RobotDriver] = {}
    for ns in namespaces:
        driver_map[ns] = RobotDriver(ns, namespaces, centroid, centroid_lock)

    for i, ns in enumerate(namespaces):
        for j, other_ns in enumerate(namespaces):
            if other_ns != ns:
                driver_map[ns].add_peer(driver_map[other_ns], DIST_MATRIX[i][j])

    drivers  = [driver_map[ns] for ns in namespaces]
    executor = MultiThreadedExecutor(num_threads=n * 2)
    for d in drivers:
        executor.add_node(d)

    last_log = 0.0

    try:
        while rclpy.ok():
            executor.spin_once(timeout_sec=DT)

            now = drivers[0].get_clock().now().nanoseconds * 1e-9
            if (now - last_log) >= 1.0:
                pairs = all_pairwise_errors(namespaces, driver_map, DIST_MATRIX)
                with centroid_lock:
                    cx, cy = centroid.x, centroid.y
                if pairs is not None:
                    pos_str = '  '.join(
                        f'{ns}=({driver_map[ns].get_position().x:.2f},'
                        f'{driver_map[ns].get_position().y:.2f})'
                        for ns in namespaces)
                    err_str = '  '.join(
                        f'|{a.strip("/")}↔{b.strip("/")}|={d:.2f}/{ds:.2f}m'
                        for a, b, d, ds in pairs)
                    print(f'[status] centroid=({cx:.2f},{cy:.2f})  '
                          f'{pos_str}  {err_str}')
                last_log = now

            if all(d.done for d in drivers):
                pairs = all_pairwise_errors(namespaces, driver_map, DIST_MATRIX)
                print('\nFormation reached.')
                for ns in namespaces:
                    p = driver_map[ns].get_position()
                    print(f'  {ns}: ({p.x:.3f}, {p.y:.3f})')
                if pairs:
                    for a, b, d, ds in pairs:
                        print(f'  |{a.strip("/")}↔{b.strip("/")}|='
                              f'{d:.3f} m  (desired {ds:.3f} m  err {abs(d-ds):.3f} m)')
                break

    except KeyboardInterrupt:
        print('\nInterrupted.')
    finally:
        stop = Twist()
        for d in drivers:
            d.cmd_pub.publish(stop)
            d.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()