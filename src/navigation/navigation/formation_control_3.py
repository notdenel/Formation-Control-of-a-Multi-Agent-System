#!/usr/bin/env python3
"""
Multi-robot formation control using APF + joystick-controlled centroid.
Robots discover each other automatically from active /robotX/odom topics.
Centroid starts at (0,0) and is moved by integrating /robotX/controller/cmd_vel
(where X is the primary/first-discovered robot's namespace).

Usage:
    ros2 run navigation formation_control_3
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
GOAL_TOLERANCE = 0.05   # m  — per-pair formation error threshold
LINEAR_SPEED   = 0.3    # m/s — capped output speed sent to controller/cmd_vel

# ── Desired inter-agent distances (metres) ────────────────────────────────────
# Row/col order matches sorted discovery order e.g. [/robot1, /robot2, /robot3].
# The matrix must be symmetric: DIST_MATRIX[i][j] == DIST_MATRIX[j][i].
# Zero on the diagonal (self-to-self).
#             robot1  robot2  robot3
DIST_MATRIX = [
    [0.0,    0.5,    0.5],   # robot1 ↔ robot2: 0.5 m, robot1 ↔ robot3: 0.5 m
    [0.5,    0.0,    0.5],   # robot2 ↔ robot1: 0.5 m, robot2 ↔ robot3: 0.5 m
    [0.5,    0.5,    0.0],   # robot3 ↔ robot1: 0.5 m, robot3 ↔ robot2: 0.5 m
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

    def __add__(self, o):     return Vec2(self.x + o.x, self.y + o.y)
    def __sub__(self, o):     return Vec2(self.x - o.x, self.y - o.y)
    def __mul__(self, s):     return Vec2(self.x * s,   self.y * s)
    def __rmul__(self, s):    return self.__mul__(s)
    def __truediv__(self, s): return Vec2(self.x / s,   self.y / s)

    def norm(self):
        return math.hypot(self.x, self.y)

    def normalized(self):
        n = self.norm()
        return Vec2(self.x / n, self.y / n) if n > 1e-9 else Vec2()


def yaw_from_quaternion(q) -> float:
    return math.atan2(
        2.0 * (q.w * q.z + q.x * q.y),
        1.0 - 2.0 * (q.y * q.y + q.z * q.z))


def natural_sort_key(s: str):
    """Sort namespaces numerically so /robot2 < /robot10."""
    return [int(c) if c.isdigit() else c.lower()
            for c in re.split(r'(\d+)', s)]


# ── DiscoveryNode ─────────────────────────────────────────────────────────────

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
        # Use natural sort so /robot2 comes before /robot10
        found = sorted(found, key=natural_sort_key)
        self.get_logger().info(f'[discovery] Found: {found}')
        return found


# ── RobotDriver ───────────────────────────────────────────────────────────────

class RobotDriver(Node):
    """
    Controls one robot.

    Centroid starts at (0,0) and is integrated from the primary robot's
    /robotX/controller/cmd_vel topic (only by the primary driver, index 0
    in the sorted namespace list) to avoid N-times over-integration.
    """

    def __init__(
        self,
        namespace:      str,
        all_namespaces: list[str],
        centroid:       Vec2,
        centroid_lock:  threading.Lock,
        is_primary:     bool = False,
        primary_ns:     str  = '',
    ):
        super().__init__(f'{namespace.strip("/")}_driver')

        self.namespace     = namespace
        self.centroid      = centroid
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

        # FIX 1: Publish to /robotX/controller/cmd_vel — this is the topic the
        # hardware driver (odom_publisher_node.py) actually subscribes to.
        # The old topic /robotX/cmd_vel has no subscriber on real hardware.
        self.cmd_pub   = self.create_publisher(Twist, f'{namespace}/controller/cmd_vel', 10)
        self.ready_pub = self.create_publisher(Bool,  f'{namespace}/ready',   10)

        self.create_subscription(Odometry, f'{namespace}/odom', self._odom_cb, 10)

        # FIX 2: Joystick topic uses the primary robot's namespaced topic.
        # The joystick node runs under namespace=robotX (e.g. robot1) and
        # therefore publishes to /robot1/controller/cmd_vel — an absolute path.
        # The old code subscribed to '/controller/cmd_vel' (no namespace prefix),
        # which is a topic no node ever publishes to, so centroid never moved.
        if is_primary:
            joy_topic = f'{primary_ns}/controller/cmd_vel'
            self.create_subscription(Twist, joy_topic, self._joy_cb, 10)
            self.get_logger().info(
                f'[{namespace}] Primary driver — joystick on {joy_topic}')

        for ns in all_namespaces:
            if ns != namespace:
                self.create_subscription(
                    Bool, f'{ns}/ready',
                    lambda msg, ns=ns: self._ready_cb(ns), 10)

        self.create_timer(DT, self._control_loop)

        # FIX 3: Periodically re-publish ready so late-joining peers don't miss
        # the single message.  /robotX/ready has no TRANSIENT_LOCAL durability,
        # so a single publish fired inside _odom_cb is lost if a peer's
        # subscriber isn't yet active — all_ready would never become True.
        self.create_timer(0.2, self._broadcast_ready)

        self.get_logger().info(
            f'[{namespace}] Driver initialised '
            f'({"primary" if is_primary else "secondary"}).')

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

    def _broadcast_ready(self) -> None:
        """FIX 3: Keep advertising readiness until all peers have confirmed."""
        if self.odom_ready and not self.all_ready:
            self.ready_pub.publish(Bool(data=True))

    def _joy_cb(self, msg: Twist) -> None:
        """Only called on the primary driver — no N-times duplication.

        /robotN/controller/cmd_vel carries BODY-frame velocity (forward in
        the robot's heading). Integrating it directly into a WORLD-frame
        centroid is wrong as soon as the primary robot rotates. Rotate the
        body-frame velocity into world frame using the primary robot's
        current yaw before integrating.
        """
        if self.current_yaw is None:
            return  # yaw not yet known — skip until first odom arrives
        c = math.cos(self.current_yaw)
        s = math.sin(self.current_yaw)
        vx_world = c * msg.linear.x - s * msg.linear.y
        vy_world = s * msg.linear.x + c * msg.linear.y
        with self.centroid_lock:
            self.centroid.x += vx_world * DT
            self.centroid.y += vy_world * DT

    def _ready_cb(self, peer_ns: str) -> None:
        if self.all_ready:
            return
        self.ready_peers.add(peer_ns)
        if self.all_namespaces.issubset(self.ready_peers):
            self.all_ready = True
            self.get_logger().info(
                f'[{self.namespace}] All peers ready — starting!')

    # ── control loop ──────────────────────────────────────────────────────────

    def _control_loop(self) -> None:
        if self.done or not self.odom_ready or not self.all_ready:
            return
        if not all(p.odom_ready for p in self.peers):
            return
        if self.start_yaw is None or self.current_yaw is None:
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

        # ── Pairwise APF ──────────────────────────────────────────────────────
        # FIX 4: Replace the 1/error² repulsion (which blows up as dist → d_star
        # from below, producing forces of 5 000 – 500 000 m/s² at 1–10 mm short)
        # with a linear-symmetric APF:
        #
        #   error = dist - d_star       (+ too far, − too close)
        #   f_on_i = G_A * error * (−unit_away)   purely linear, no singularity
        #
        # "unit_away" is the unit vector pointing FROM peer j TO self i.
        # Negating it means:
        #   error > 0 (too far)  → force is in the −unit_away direction → toward j ✓
        #   error < 0 (too close) → force is in the +unit_away direction → away from j ✓
        #
        # G_R is no longer needed for the pairwise term (removed); the linear
        # law is inherently repulsive below d_star without a separate 1/r² term.
        errors = []
        for pos_peer, d_star in zip(peer_positions, self.desired_dists):
            dx   = pos_self.x - pos_peer.x
            dy   = pos_self.y - pos_peer.y
            dist = math.hypot(dx, dy)

            if dist < 1e-6:
                errors.append(0.0)
                continue

            error = dist - d_star   # + too far, − too close
            errors.append(abs(error))

            if abs(error) < 1e-9:
                continue

            # Unit vector pointing FROM peer TO self (away from peer)
            ux = dx / dist
            uy = dy / dist

            # Linear APF: negative sign pulls self toward peer when too far,
            # positive sign pushes self away when too close.
            f.x += -G_A * error * ux
            f.y += -G_A * error * uy

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

        # ── Per-axis clamp to keep mecanum wheel loads balanced ───────────────
        mx = LINEAR_SPEED / math.sqrt(2)
        lx = max(-mx, min(mx, lx))
        ly = max(-mx, min(mx, ly))

        # ── Yaw-drift correction ──────────────────────────────────────────────
        yaw_err = wrap_angle(self.current_yaw - self.start_yaw)
        wz = 0.0
        if abs(yaw_err) > YAW_CORRECTION_THRESH_RAD:
            wz = max(-YAW_CORRECTION_MAX_RAD_S,
                     min(YAW_CORRECTION_MAX_RAD_S,
                         -YAW_CORRECTION_GAIN * yaw_err))

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
        driver_map:  dict[str, 'RobotDriver'],
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
            out.append((a, b, math.hypot(pa.x - pb.x, pa.y - pb.y),
                        dist_matrix[i][j]))
    return out


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    rclpy.init()

    discovery  = DiscoveryNode()
    namespaces = discovery.discover(timeout_sec=5.0)
    discovery.destroy_node()

    if len(namespaces) < 2:
        print(f'[formation_control_3] Need ≥2 robots, found {len(namespaces)}. Aborting.')
        rclpy.shutdown()
        return

    n = len(namespaces)

    if len(DIST_MATRIX) < n or any(len(r) < n for r in DIST_MATRIX):
        print(f'[formation_control_3] DIST_MATRIX too small for {n} robots. Aborting.')
        rclpy.shutdown()
        return

    # Primary namespace is the first in sorted order (e.g. /robot1).
    # The joystick is expected to run in that robot's namespace.
    primary_ns = namespaces[0]

    print(f'\nFormation control: {" ↔ ".join(namespaces)}')
    print('Desired distances:')
    for i, a in enumerate(namespaces):
        for j, b in enumerate(namespaces):
            if j <= i:
                continue
            print(f'  {a} ↔ {b}: {DIST_MATRIX[i][j]:.3f} m')
    print(f'Centroid: (0.00, 0.00) — move with joystick on '
          f'{primary_ns}/controller/cmd_vel\n')

    # Shared centroid — all drivers hold a reference to the same object
    centroid      = Vec2(0.0, 0.0)
    centroid_lock = threading.Lock()

    driver_map: dict[str, RobotDriver] = {}
    for idx, ns in enumerate(namespaces):
        driver_map[ns] = RobotDriver(
            ns, namespaces, centroid, centroid_lock,
            is_primary=(idx == 0),
            primary_ns=primary_ns,
        )

    # Wire peers: use DIST_MATRIX[i][j] indexed by sorted namespace order,
    # consistent across all robots.
    for i, ns in enumerate(namespaces):
        for j, other_ns in enumerate(namespaces):
            if other_ns != ns:
                driver_map[ns].add_peer(
                    driver_map[other_ns], DIST_MATRIX[i][j])

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
                        f'|{a.strip("/"):}↔{b.strip("/")}|={d:.2f}/{ds:.2f}m'
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
                        print(f'  |{a.strip("/"):}↔{b.strip("/")}|='
                              f'{d:.3f} m  (desired {ds:.3f} m  '
                              f'err {abs(d - ds):.3f} m)')
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