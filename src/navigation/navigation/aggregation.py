#!/usr/bin/env python3
"""
aggregation.py
==============
On-robot multi-robot aggregation using APF (Artificial Potential Field).
Runs in each robot's private domain; peer positions arrive via odom_bridge.

Architecture:
  Each robot runs this node.  Discovery finds all live /robotX/odom topics by
  verifying actual message flow (not just topic existence), which filters out
  bridge ghost endpoints that have a publisher but no upstream data source.

  One RobotDriver is created per discovered robot.  The driver for THIS robot
  publishes /robotX/controller/cmd_vel locally.  Drivers for peer robots also
  publish cmd_vel — those publishers have no subscriber in this domain, which
  is harmless.  Each robot controls only itself based on the APF computed from
  all positions.

Discovery → APF flow:
  1. Scan for /robotX/odom topics.
  2. Subscribe to each candidate and wait up to 3 s for a real message.
  3. Build RobotDriver + PeerState objects once all live robots are confirmed.
  4. Each driver's control loop computes:
       F_i = Σ_{j≠i}  G_A * error_ij * (-unit_away_ij)
     where error_ij = dist(i,j) - GOAL_TOLERANCE.
  5. Normalise → unit direction, scale to LINEAR_SPEED.
  6. Rotate world-frame velocity into body frame (mecanum strafe).
  7. Correct yaw drift (hold heading constant throughout aggregation).

Usage (called automatically by real_robot.launch.py after 20 s delay):
  ros2 run navigation aggregation
"""

import math
import re
import threading

import rclpy
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry


# ── Motion parameters ─────────────────────────────────────────────────────────
GOAL_TOLERANCE = 0.40       # m — stop when all pairwise distances are below this
LINEAR_SPEED   = 0.3        # m/s

YAW_GAIN     = 1.0
YAW_MAX      = 0.5          # rad/s
YAW_DEADBAND = 0.05         # rad (~3°)


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

    def __sub__(self, o):     return Vec2(self.x - o.x, self.y - o.y)
    def __add__(self, o):     return Vec2(self.x + o.x, self.y + o.y)
    def __mul__(self, s):     return Vec2(self.x * s,   self.y * s)
    def __neg__(self):        return Vec2(-self.x,      -self.y)
    def __truediv__(self, s): return Vec2(self.x / s,   self.y / s)

    def norm(self) -> float:
        return math.hypot(self.x, self.y)

    def normalized(self) -> 'Vec2':
        n = self.norm()
        return self / n if n > 1e-9 else Vec2()


# ── PeerState ─────────────────────────────────────────────────────────────────

class PeerState:
    """Thread-safe position store for one robot namespace."""

    def __init__(self, namespace: str):
        self.namespace = namespace
        self._lock = threading.Lock()
        self._pos: Vec2 | None = None
        self.ready = False

    def update(self, x: float, y: float) -> None:
        with self._lock:
            self._pos = Vec2(x, y)
            self.ready = True

    def get_position(self) -> 'Vec2 | None':
        with self._lock:
            return self._pos


# ── DiscoveryNode ─────────────────────────────────────────────────────────────

class DiscoveryNode(Node):
    """
    Two-phase discovery:
    1. Wait for /robotX/odom topics to appear in the graph.
    2. Subscribe to each and wait for at least one real message (liveness check).
       Bridge ghost endpoints advertise a publisher but never emit data, so
       robots that are offline are filtered out in this phase.
    """

    _ODOM_RE = re.compile(r'^(/robot\w+)/odom$')

    def __init__(self):
        super().__init__('aggregation_discovery')

    def discover(self, graph_timeout: float = 5.0, live_timeout: float = 3.0) -> list[str]:
        # Phase 1: wait for topic names.
        deadline = self.get_clock().now().nanoseconds * 1e-9 + graph_timeout
        candidates: list[str] = []
        while self.get_clock().now().nanoseconds * 1e-9 < deadline:
            candidates = sorted({
                m.group(1)
                for t, _ in self.get_topic_names_and_types()
                if (m := self._ODOM_RE.match(t))
            })
            if len(candidates) >= 2:
                break
            rclpy.spin_once(self, timeout_sec=0.2)

        if not candidates:
            self.get_logger().warn('[discovery] No /robotX/odom topics found.')
            return []

        # Phase 2: verify liveness by waiting for actual messages.
        live: set[str] = set()
        lock = threading.Lock()
        subs = []

        for ns in candidates:
            def _cb(msg, ns=ns):
                with lock:
                    live.add(ns)
            subs.append(self.create_subscription(Odometry, f'{ns}/odom', _cb, 10))

        live_deadline = self.get_clock().now().nanoseconds * 1e-9 + live_timeout
        while self.get_clock().now().nanoseconds * 1e-9 < live_deadline:
            rclpy.spin_once(self, timeout_sec=0.1)
            with lock:
                if live == set(candidates):
                    break

        for sub in subs:
            self.destroy_subscription(sub)

        with lock:
            found = sorted(live)

        self.get_logger().info(
            f'[discovery] Candidates={candidates}  Live={found}')
        return found


# ── RobotDriver ───────────────────────────────────────────────────────────────

class RobotDriver(Node):
    """
    Subscribes to /robotX/odom, computes APF force using all peer positions,
    and publishes /robotX/controller/cmd_vel.

    Peers are injected after construction via add_peer().  Control begins as
    soon as all PeerState.ready flags are set (first odom message received
    from every peer).
    """

    def __init__(self, namespace: str):
        super().__init__(f'{namespace.strip("/")}_driver')

        self.namespace = namespace
        self.peers: list[PeerState] = []

        self._lock = threading.Lock()
        self._pos: Vec2 | None = None
        self.yaw: float | None = None
        self.start_yaw: float | None = None
        self.odom_ready = False
        self.done = False

        self.cmd_pub = self.create_publisher(
            Twist, f'{namespace}/controller/cmd_vel', 10)

        self.create_subscription(
            Odometry, f'{namespace}/odom', self._odom_cb, 10)
        self.create_timer(0.05, self._control_loop)

        self.get_logger().info(f'[{namespace}] Driver ready.')

    def add_peer(self, peer: PeerState) -> None:
        self.peers.append(peer)

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

    def _control_loop(self) -> None:
        if self.done or not self.odom_ready:
            return
        if not all(p.ready for p in self.peers):
            return
        if self.start_yaw is None or self.yaw is None:
            return

        pos_self = self.get_position()
        if pos_self is None:
            return

        f_total = Vec2()
        distances: list[float] = []

        for peer in self.peers:
            pos_peer = peer.get_position()
            if pos_peer is None:
                return

            delta = pos_self - pos_peer
            dist = delta.norm()
            distances.append(dist)

            if dist < 1e-6:
                continue

            # Unit vector toward peer — speed is fixed at LINEAR_SPEED after
            # normalisation, so magnitude here only matters for multi-peer
            # direction blending.
            f_total = f_total + (-delta.normalized())

        if all(d < GOAL_TOLERANCE for d in distances):
            self.cmd_pub.publish(Twist())
            self.done = True
            self.get_logger().info(
                f'[{self.namespace}] Aggregation complete! '
                f'dists={[f"{d:.3f}" for d in distances]}')
            return

        fn = f_total.norm()
        if fn < 1e-6:
            return

        world_vel = f_total / fn * LINEAR_SPEED

        # World → body frame (mecanum: can strafe without rotating).
        c = math.cos(self.yaw)
        s = math.sin(self.yaw)
        lx =  c * world_vel.x + s * world_vel.y
        ly = -s * world_vel.x + c * world_vel.y

        mx = LINEAR_SPEED / math.sqrt(2)
        lx = max(-mx, min(mx, lx))
        ly = max(-mx, min(mx, ly))

        # Yaw-drift correction: maintain heading from start.
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
            f'[{self.namespace}] dists={[f"{d:.3f}" for d in distances]} '
            f'vx={lx:.3f} vy={ly:.3f}',
            throttle_duration_sec=0.5,
        )


# ── Main ──────────────────────────────────────────────────────────────────────

def _all_pairwise(
        drivers: list[RobotDriver],
        peers: dict[str, PeerState],
) -> 'list[tuple] | None':
    result = []
    ns_list = [d.namespace for d in drivers]
    for i, a in enumerate(ns_list):
        for b in ns_list[i + 1:]:
            pa = peers[a].get_position()
            pb = peers[b].get_position()
            if pa is None or pb is None:
                return None
            result.append((a, b, (pa - pb).norm()))
    return result


def main() -> None:
    rclpy.init()

    discovery = DiscoveryNode()
    namespaces = discovery.discover(graph_timeout=5.0, live_timeout=3.0)
    discovery.destroy_node()

    if len(namespaces) < 1:
        print('[aggregation] No live robots found. Aborting.')
        rclpy.shutdown()
        return

    if len(namespaces) == 1:
        print(f'[aggregation] Only one robot found ({namespaces[0]}). Need ≥2 for aggregation. Exiting.')
        rclpy.shutdown()
        return

    print(f'\n[aggregation] Starting for: {" ↔ ".join(namespaces)}\n'
          f'Goal tolerance: {GOAL_TOLERANCE:.3f} m\n')

    peer_states: dict[str, PeerState] = {ns: PeerState(ns) for ns in namespaces}

    drivers: list[RobotDriver] = []
    for ns in namespaces:
        driver = RobotDriver(ns)
        for other_ns, state in peer_states.items():
            if other_ns != ns:
                driver.add_peer(state)
        drivers.append(driver)

    # Wire odom → PeerState so shared position store stays current.
    for driver in drivers:
        state = peer_states[driver.namespace]
        orig_cb = driver._odom_cb

        def _make_cb(orig, s):
            def cb(msg):
                orig(msg)
                s.update(msg.pose.pose.position.x, msg.pose.pose.position.y)
            return cb

        driver._odom_cb = _make_cb(orig_cb, state)
        driver.create_subscription(
            Odometry, f'{driver.namespace}/odom', driver._odom_cb, 10)

    executor = MultiThreadedExecutor(num_threads=len(drivers) * 2)
    for d in drivers:
        executor.add_node(d)

    last_log = 0.0

    try:
        while rclpy.ok():
            executor.spin_once(timeout_sec=0.05)

            now = drivers[0].get_clock().now().nanoseconds * 1e-9
            if now - last_log >= 1.0:
                pairs = _all_pairwise(drivers, peer_states)
                if pairs is not None:
                    pos_s = '  '.join(
                        f'{ns}=({peer_states[ns].get_position().x:.3f},'
                        f'{peer_states[ns].get_position().y:.3f})'
                        for ns in namespaces)
                    dist_s = '  '.join(
                        f'|{a.strip("/")}↔{b.strip("/")}|={d:.3f}m'
                        for a, b, d in pairs)
                    print(f'[status] {pos_s}  {dist_s}')
                last_log = now

            if all(d.done for d in drivers):
                pairs = _all_pairwise(drivers, peer_states)
                print('\nAll robots aggregated.')
                for ns in namespaces:
                    p = peer_states[ns].get_position()
                    print(f'  {ns}: ({p.x:.3f}, {p.y:.3f})')
                if pairs:
                    for a, b, d in pairs:
                        print(f'  |{a.strip("/")}↔{b.strip("/")}| = {d:.3f} m')
                break

    except KeyboardInterrupt:
        print('\nInterrupted.')
    finally:
        stop = Twist()
        for d in drivers:
            for _ in range(6):
                d.cmd_pub.publish(stop)
                executor.spin_once(timeout_sec=0.05)
        for d in drivers:
            d.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
