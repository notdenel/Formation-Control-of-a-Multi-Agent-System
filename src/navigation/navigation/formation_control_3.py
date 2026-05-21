#!/usr/bin/env python3
"""
formation_control_3.py
======================
N-robot formation control with APF and joystick-driven centroid.

Robots auto-discover each other from live /robotX/odom topics.  The centroid
starts at (0, 0) and is moved by integrating velocity commands arriving on
the primary robot's /robotX/controller/cmd_vel topic (joystick or teleop).

Each robot drives to maintain its desired spacing from all peers while
following the moving centroid.  The DIST_MATRIX defines per-pair desired
distances and must be symmetric.

Usage:
  ros2 run navigation formation_control_3

Adjust DIST_MATRIX below for your formation geometry.
"""

import math
import re
import threading

import rclpy
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from std_msgs.msg import Bool


# ── Formation geometry ────────────────────────────────────────────────────────
# Row/column order matches sorted discovery order: [/robot1, /robot2, /robot3].
# DIST_MATRIX[i][j] is the desired distance between robots i and j (metres).
# The matrix must be symmetric; zeros on the diagonal.
#             robot1  robot2  robot3
DIST_MATRIX = [
    [0.0,    0.5,    0.5],
    [0.5,    0.0,    0.5],
    [0.5,    0.5,    0.0],
]

# ── APF and motion parameters ─────────────────────────────────────────────────
G_A            = 10.0
G_TRACK        = 1.0    # centroid tracking gain
GOAL_TOLERANCE = 0.05   # m — formation error threshold per pair
LINEAR_SPEED   = 0.3    # m/s

DT = 0.05   # control loop period (s)

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


def natural_sort_key(s: str):
    return [int(c) if c.isdigit() else c.lower()
            for c in re.split(r'(\d+)', s)]


class Vec2:
    __slots__ = ('x', 'y')

    def __init__(self, x: float = 0.0, y: float = 0.0):
        self.x = x
        self.y = y

    def __add__(self, o):     return Vec2(self.x + o.x, self.y + o.y)
    def __sub__(self, o):     return Vec2(self.x - o.x, self.y - o.y)
    def __mul__(self, s):     return Vec2(self.x * s,   self.y * s)
    def __truediv__(self, s): return Vec2(self.x / s,   self.y / s)

    def norm(self) -> float:
        return math.hypot(self.x, self.y)

    def normalized(self) -> 'Vec2':
        n = self.norm()
        return Vec2(self.x / n, self.y / n) if n > 1e-9 else Vec2()


# ── DiscoveryNode ─────────────────────────────────────────────────────────────

class DiscoveryNode(Node):
    _ODOM_RE = re.compile(r'^(/robot\w+)/odom$')

    def __init__(self):
        super().__init__('fc3_discovery')

    def discover(self, timeout_sec: float = 5.0) -> list[str]:
        deadline = self.get_clock().now().nanoseconds * 1e-9 + timeout_sec
        found: list[str] = []
        while self.get_clock().now().nanoseconds * 1e-9 < deadline:
            found = [
                m.group(1)
                for t, _ in self.get_topic_names_and_types()
                if (m := self._ODOM_RE.match(t))
            ]
            if len(found) >= 2:
                break
            rclpy.spin_once(self, timeout_sec=0.2)
        found = sorted(found, key=natural_sort_key)
        self.get_logger().info(f'[discovery] Found: {found}')
        return found


# ── RobotDriver ───────────────────────────────────────────────────────────────

class RobotDriver(Node):
    """
    Controls one robot in an N-robot formation.

    The centroid is a mutable Vec2 shared (by reference) across all drivers.
    Only the primary driver (index 0 in sorted order) integrates joystick
    commands into the centroid to avoid N-times over-integration.

    APF force on robot i:
      F_i = G_TRACK * (centroid - xi)                   (tracking term)
          + Σ_{j≠i}  -G_A * error_ij * unit_away_ij     (pairwise formation)
    where error_ij = dist(i,j) - DIST_MATRIX[i][j].
    """

    def __init__(
        self,
        namespace:     str,
        all_namespaces: list[str],
        centroid:      Vec2,
        centroid_lock: threading.Lock,
        is_primary:    bool,
        primary_ns:    str,
    ):
        super().__init__(f'{namespace.strip("/")}_fc3_driver')

        self.namespace     = namespace
        self.centroid      = centroid
        self.centroid_lock = centroid_lock

        self.peers: list['RobotDriver'] = []
        self.desired_dists: list[float] = []

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

        if is_primary:
            self.create_subscription(
                Twist, f'{primary_ns}/controller/cmd_vel',
                self._joy_cb, 10)
            self.get_logger().info(
                f'[{namespace}] Primary driver — '
                f'centroid driven by {primary_ns}/controller/cmd_vel')

        for ns in all_namespaces:
            if ns != namespace:
                self.create_subscription(
                    Bool, f'{ns}/ready',
                    lambda msg, ns=ns: self._ready_cb(ns), 10)

        self.create_timer(DT, self._control_loop)
        self.create_timer(0.2, self._broadcast_ready)

        self.get_logger().info(
            f'[{namespace}] FC3 driver ready '
            f'({"primary" if is_primary else "secondary"}).')

    def add_peer(self, peer: 'RobotDriver', desired_dist: float) -> None:
        self.peers.append(peer)
        self.desired_dists.append(desired_dist)

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

    def _joy_cb(self, msg: Twist) -> None:
        if self.yaw is None:
            return
        # Rotate body-frame velocity into world frame before integrating.
        c = math.cos(self.yaw)
        s = math.sin(self.yaw)
        with self.centroid_lock:
            self.centroid.x += (c * msg.linear.x - s * msg.linear.y) * DT
            self.centroid.y += (s * msg.linear.x + c * msg.linear.y) * DT

    def _ready_cb(self, peer_ns: str) -> None:
        if self.all_ready:
            return
        self.ready_peers.add(peer_ns)
        if self.all_namespaces.issubset(self.ready_peers):
            self.all_ready = True
            self.get_logger().info(
                f'[{self.namespace}] All peers ready — starting!')

    def _control_loop(self) -> None:
        if self.done or not self.odom_ready or not self.all_ready:
            return
        if not all(p.odom_ready for p in self.peers):
            return
        if self.start_yaw is None or self.yaw is None:
            return

        pos_self = self.get_position()
        if pos_self is None:
            return

        peer_positions: list[Vec2] = []
        for peer in self.peers:
            pp = peer.get_position()
            if pp is None:
                return
            peer_positions.append(pp)

        with self.centroid_lock:
            cx, cy = self.centroid.x, self.centroid.y

        # Centroid tracking force.
        f = Vec2(G_TRACK * (cx - pos_self.x), G_TRACK * (cy - pos_self.y))

        # Pairwise APF: linear symmetric law, no singularity.
        errors: list[float] = []
        for pos_peer, d_star in zip(peer_positions, self.desired_dists):
            dx = pos_self.x - pos_peer.x
            dy = pos_self.y - pos_peer.y
            dist = math.hypot(dx, dy)

            if dist < 1e-6:
                errors.append(0.0)
                continue

            error = dist - d_star
            errors.append(abs(error))

            if abs(error) < 1e-9:
                continue

            ux = dx / dist
            uy = dy / dist
            f.x += -G_A * error * ux
            f.y += -G_A * error * uy

        if all(e < GOAL_TOLERANCE for e in errors):
            self.cmd_pub.publish(Twist())
            self.done = True
            self.get_logger().info(
                f'[{self.namespace}] Formation reached! '
                f'errors={[f"{e:.3f}" for e in errors]}')
            return

        fn = math.hypot(f.x, f.y)
        if fn < 1e-6:
            return

        wx = f.x / fn * LINEAR_SPEED
        wy = f.y / fn * LINEAR_SPEED

        c = math.cos(self.yaw)
        s = math.sin(self.yaw)
        lx =  c * wx + s * wy
        ly = -s * wx + c * wy

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
            f'[{self.namespace}] errors={[f"{e:.3f}" for e in errors]} '
            f'centroid=({cx:.2f},{cy:.2f}) vx={lx:.3f} vy={ly:.3f}',
            throttle_duration_sec=0.5)


# ── Utility ───────────────────────────────────────────────────────────────────

def _pairwise_errors(
        namespaces: list[str],
        driver_map: dict[str, RobotDriver],
        dist_matrix: list[list[float]],
) -> 'list[tuple] | None':
    result = []
    for i, a in enumerate(namespaces):
        for j, b in enumerate(namespaces):
            if j <= i:
                continue
            pa = driver_map[a].get_position()
            pb = driver_map[b].get_position()
            if pa is None or pb is None:
                return None
            result.append((a, b, math.hypot(pa.x - pb.x, pa.y - pb.y),
                           dist_matrix[i][j]))
    return result


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    rclpy.init()

    disc = DiscoveryNode()
    namespaces = disc.discover(timeout_sec=5.0)
    disc.destroy_node()

    if len(namespaces) < 2:
        print(f'[fc3] Need ≥2 robots, found {len(namespaces)}. Aborting.')
        rclpy.shutdown()
        return

    n = len(namespaces)
    if len(DIST_MATRIX) < n or any(len(r) < n for r in DIST_MATRIX):
        print(f'[fc3] DIST_MATRIX too small for {n} robots. Aborting.')
        rclpy.shutdown()
        return

    primary_ns = namespaces[0]

    print(f'\nFormation control: {" ↔ ".join(namespaces)}')
    print('Desired distances:')
    for i, a in enumerate(namespaces):
        for j, b in enumerate(namespaces):
            if j <= i:
                continue
            print(f'  {a} ↔ {b}: {DIST_MATRIX[i][j]:.3f} m')
    print(f'Centroid: (0.00, 0.00) — '
          f'move via {primary_ns}/controller/cmd_vel\n')

    centroid = Vec2(0.0, 0.0)
    centroid_lock = threading.Lock()

    driver_map: dict[str, RobotDriver] = {}
    for idx, ns in enumerate(namespaces):
        driver_map[ns] = RobotDriver(
            ns, namespaces, centroid, centroid_lock,
            is_primary=(idx == 0),
            primary_ns=primary_ns,
        )

    for i, ns in enumerate(namespaces):
        for j, other_ns in enumerate(namespaces):
            if other_ns != ns:
                driver_map[ns].add_peer(driver_map[other_ns], DIST_MATRIX[i][j])

    drivers = [driver_map[ns] for ns in namespaces]
    executor = MultiThreadedExecutor(num_threads=n * 2)
    for d in drivers:
        executor.add_node(d)

    last_log = 0.0

    try:
        while rclpy.ok():
            executor.spin_once(timeout_sec=DT)

            now = drivers[0].get_clock().now().nanoseconds * 1e-9
            if now - last_log >= 1.0:
                pairs = _pairwise_errors(namespaces, driver_map, DIST_MATRIX)
                with centroid_lock:
                    cx, cy = centroid.x, centroid.y
                if pairs is not None:
                    pos_s = '  '.join(
                        f'{ns}=({driver_map[ns].get_position().x:.2f},'
                        f'{driver_map[ns].get_position().y:.2f})'
                        for ns in namespaces)
                    err_s = '  '.join(
                        f'|{a.strip("/")}↔{b.strip("/")}|={d:.2f}/{ds:.2f}m'
                        for a, b, d, ds in pairs)
                    print(f'[status] centroid=({cx:.2f},{cy:.2f})  '
                          f'{pos_s}  {err_s}')
                last_log = now

            if all(d.done for d in drivers):
                pairs = _pairwise_errors(namespaces, driver_map, DIST_MATRIX)
                print('\nFormation reached.')
                for ns in namespaces:
                    p = driver_map[ns].get_position()
                    print(f'  {ns}: ({p.x:.3f},{p.y:.3f})')
                if pairs:
                    for a, b, d, ds in pairs:
                        print(f'  |{a.strip("/")}↔{b.strip("/")}|='
                              f'{d:.3f}m  (desired {ds:.3f}m  '
                              f'err {abs(d-ds):.3f}m)')
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
