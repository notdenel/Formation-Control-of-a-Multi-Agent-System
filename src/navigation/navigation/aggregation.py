#!/usr/bin/env python3
"""
Automatic multi-robot aggregation using APF + odometry feedback.
Robots are discovered automatically from active /robotX/odom topics.
No parameters needed — peers are discovered from the ROS graph.

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
G_A = 10.0  # attraction gain  (toward peer)
G_R = 0.5   # repulsion gain   (away from peer at close range)

GOAL_TOLERANCE = (G_R / G_A) ** (1 / 3)   # natural equilibrium ≈ 0.368 m

# Yaw-drift correction
YAW_CORRECTION_GAIN       = 1.0
YAW_CORRECTION_MAX_RAD_S  = 0.5
YAW_CORRECTION_THRESH_RAD = 0.05


# ── Helpers ───────────────────────────────────────────────────────────────────

def wrap_angle(angle: float) -> float:
    return math.atan2(math.sin(angle), math.cos(angle))


class Vec2:
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


# ── Peer state (shared position store) ───────────────────────────────────────

class PeerState:
    """
    Lightweight position store for a peer discovered from the ROS graph.
    One instance per peer namespace, shared across all RobotDrivers.
    """
    def __init__(self, namespace: str):
        self.namespace = namespace
        self._lock     = threading.Lock()
        self._pos: Vec2 | None = None
        self.ready     = False

    def update(self, x: float, y: float) -> None:
        with self._lock:
            self._pos  = Vec2(x, y)
            self.ready = True

    def get_position(self) -> 'Vec2 | None':
        with self._lock:
            return self._pos


# ── Discovery node ────────────────────────────────────────────────────────────

class DiscoveryNode(Node):
    """
    Scans the ROS graph once for active /robotX/odom topics.
    Returns the list of discovered namespaces.
    """
    ODOM_PATTERN = re.compile(r'^(/robot\w+)/odom$')

    def __init__(self):
        super().__init__('aggregation_discovery')

    def discover(self, timeout_sec: float = 3.0) -> list[str]:
        """Block until at least 2 robots are found or timeout expires."""
        deadline = self.get_clock().now().nanoseconds * 1e-9 + timeout_sec
        namespaces: list[str] = []

        while self.get_clock().now().nanoseconds * 1e-9 < deadline:
            topics = self.get_topic_names_and_types()
            namespaces = [
                m.group(1)
                for topic, _ in topics
                if (m := self.ODOM_PATTERN.match(topic))
            ]
            if len(namespaces) >= 2:
                break
            rclpy.spin_once(self, timeout_sec=0.2)

        self.get_logger().info(
            f'[discovery] Found {len(namespaces)} robot(s): {namespaces}')
        return sorted(namespaces)


# ── RobotDriver ───────────────────────────────────────────────────────────────

class RobotDriver(Node):
    """
    Controls one robot namespace.
    Peers are injected as PeerState objects after discovery.
    Implements: J_i(x) = Σ_{j≠i} [ J_a(||xi-xj||) - J_r(||xi-xj||) ]
    """

    def __init__(self, namespace: str, all_namespaces: list[str]):
        super().__init__(f'{namespace.strip("/")}_driver')

        self.namespace = namespace
        self.peers: list[PeerState] = []   # injected via add_peer()

        # ── thread-safe own position ──────────────────────────────────────────
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
        self.cmd_pub   = self.create_publisher(Twist, f'{namespace}/controller/cmd_vel', 10)
        self.ready_pub = self.create_publisher(Bool,  f'{namespace}/ready',   10)

        # NOTE: The odom subscription is intentionally deferred.
        # main() patches _odom_cb to also update the shared PeerState, then
        # registers the single subscription with the patched callback.
        # Do NOT add a subscription here — it would create a second subscriber
        # with the original (un-patched) callback, leaving PeerState unpopulated
        # for the other drivers while also running the control loop on stale data.

        for ns in all_namespaces:
            if ns != namespace:
                self.create_subscription(
                    Bool, f'{ns}/ready',
                    lambda msg, ns=ns: self._ready_cb(ns),
                    10)

        self.create_timer(0.05, self._control_loop)
        # Re-broadcast our ready signal at 5 Hz until all peers have seen it.
        # Without this, a peer that subscribes after our first odom callback
        # would never receive the Bool(True) and all_ready would never trigger.
        self.create_timer(0.2, self._broadcast_ready)
        self.get_logger().info(f'[{namespace}] Driver initialised.')

    # ── public API ────────────────────────────────────────────────────────────

    def add_peer(self, peer: PeerState) -> None:
        self.peers.append(peer)

    def get_position(self) -> 'Vec2 | None':
        with self._pos_lock:
            return self._pos

    # ── ROS callbacks ─────────────────────────────────────────────────────────

    def _broadcast_ready(self) -> None:
        """Repeatedly advertise our ready state until all peers have seen it."""
        if self.odom_ready and not self.all_ready:
            self.ready_pub.publish(Bool(data=True))

    def _odom_cb(self, msg: Odometry) -> None:
        pose = msg.pose.pose

        with self._pos_lock:
            self._pos = Vec2(pose.position.x, pose.position.y)

        self.current_yaw = yaw_from_quaternion(pose.orientation)
        self.odom_ready  = True

        if self.start_yaw is None:
            self.start_yaw = self.current_yaw

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
        if not all(p.ready for p in self.peers):
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

            delta    = pos_self - pos_peer
            distance = delta.norm()
            distances.append(distance)

            if distance < 1e-6:
                continue

            direction = delta.normalized()

            # Linear-symmetric APF (matches formation_control_3.py).
            # The old 1/r^2 repulsion blew up to ~50 m/s² at d=0.1 m and
            # alternated sign rapidly across GOAL_TOLERANCE ≈ 0.368 m,
            # producing oscillation near equilibrium.
            #   error = distance - GOAL_TOLERANCE  (+ too far, − too close)
            #   too far  → force toward peer
            #   too close → force away from peer
            error = distance - GOAL_TOLERANCE
            f_total = f_total + (-direction) * G_A * error

        # ── Goal check ────────────────────────────────────────────────────────
        if all(d < GOAL_TOLERANCE for d in distances):
            self.cmd_pub.publish(Twist())
            self.done = True
            self.get_logger().info(
                f'[{self.namespace}] Aggregation complete! '
                f'dists={[f"{d:.3f}" for d in distances]}')
            return

        # ── Normalize → unit direction ────────────────────────────────────────
        f_norm = f_total.norm()
        if f_norm < 1e-6:
            return

        # Match formation_control.py and formation_control_3.py and stay
        # inside the EKF acceleration_limits envelope (1.3 m/s²).
        LINEAR_SPEED = 0.3   # m/s — sets scale; APF gives the direction
        world_vel    = f_total / f_norm * LINEAR_SPEED

        # ── World → body-frame ────────────────────────────────────────────────
        c = math.cos(self.current_yaw)
        s = math.sin(self.current_yaw)

        local_x =  c * world_vel.x + s * world_vel.y
        local_y = -s * world_vel.x + c * world_vel.y

        # ── Per-axis clamp — equalises mecanum wheel load ─────────────────────
        max_axis = LINEAR_SPEED / math.sqrt(2)
        local_x  = max(-max_axis, min(max_axis, local_x))
        local_y  = max(-max_axis, min(max_axis, local_y))

        # ── Yaw-drift correction ──────────────────────────────────────────────
        yaw_error = wrap_angle(self.current_yaw - self.start_yaw)
        wz = 0.0
        if abs(yaw_error) > YAW_CORRECTION_THRESH_RAD:
            wz = max(
                -YAW_CORRECTION_MAX_RAD_S,
                min(YAW_CORRECTION_MAX_RAD_S, -YAW_CORRECTION_GAIN * yaw_error),
            )

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

def all_pairwise_distances(
        drivers: list[RobotDriver],
        peers:   dict[str, PeerState]
) -> list[tuple[str, str, float]] | None:
    results = []
    ns_list = [d.namespace for d in drivers]
    for i, ns_a in enumerate(ns_list):
        for ns_b in ns_list[i + 1:]:
            pa = peers[ns_a].get_position()
            pb = peers[ns_b].get_position()
            if pa is None or pb is None:
                return None
            results.append((ns_a, ns_b, (pa - pb).norm()))
    return results


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    rclpy.init()

    # ── 1. Discover robots ────────────────────────────────────────────────────
    discovery = DiscoveryNode()
    namespaces = discovery.discover(timeout_sec=5.0)
    discovery.destroy_node()

    if len(namespaces) < 2:
        print(f'[aggregation] Need at least 2 robots, found {len(namespaces)}. Aborting.')
        rclpy.shutdown()
        return

    print(f'\nStarting aggregation for: {" ↔ ".join(namespaces)}\n'
          f'Equilibrium distance: {GOAL_TOLERANCE:.3f} m\n')

    # ── 2. Build shared PeerState map (one per namespace) ─────────────────────
    # Each PeerState is a lightweight shared position store subscribed to
    # by a single OdomRelay node, then read by all other RobotDrivers.
    peer_states: dict[str, PeerState] = {ns: PeerState(ns) for ns in namespaces}

    # ── 3. Build one RobotDriver per namespace ────────────────────────────────
    drivers: list[RobotDriver] = []
    for ns in namespaces:
        driver = RobotDriver(ns, namespaces)
        for other_ns, state in peer_states.items():
            if other_ns != ns:
                driver.add_peer(state)
        drivers.append(driver)

    # ── 4. Wire odom → PeerState (each driver updates its own PeerState) ──────
    # Re-use the driver's own _odom_cb to also push into the shared store.
    # We patch post-construction so PeerState is populated for all peers.
    for driver in drivers:
        state = peer_states[driver.namespace]
        original_cb = driver._odom_cb

        def make_cb(orig, s):
            def cb(msg):
                orig(msg)
                s.update(msg.pose.pose.position.x, msg.pose.pose.position.y)
            return cb

        driver._odom_cb = make_cb(original_cb, state)
        # Re-register subscription with patched callback
        driver.create_subscription(
            Odometry, f'{driver.namespace}/odom', driver._odom_cb, 10)

    # ── 5. Spin ───────────────────────────────────────────────────────────────
    executor = MultiThreadedExecutor(num_threads=len(drivers) * 2)
    for driver in drivers:
        executor.add_node(driver)

    last_log = 0.0

    try:
        while rclpy.ok():
            executor.spin_once(timeout_sec=0.05)

            now = drivers[0].get_clock().now().nanoseconds * 1e-9
            if (now - last_log) >= 1.0:
                dists = all_pairwise_distances(drivers, peer_states)
                if dists is not None:
                    pos_strs = '  '.join(
                        f'{ns}=({peer_states[ns].get_position().x:.3f},'
                        f'{peer_states[ns].get_position().y:.3f})'
                        for ns in namespaces
                    )
                    dist_strs = '  '.join(
                        f'|{a.strip("/")}↔{b.strip("/")}|={d:.3f}m'
                        for a, b, d in dists
                    )
                    print(f'[status]  {pos_strs}  {dist_strs}')
                last_log = now

            if all(d.done for d in drivers):
                dists = all_pairwise_distances(drivers, peer_states)
                print(f'\nAll robots aggregated.')
                for ns in namespaces:
                    p = peer_states[ns].get_position()
                    print(f'  {ns} final: ({p.x:.3f}, {p.y:.3f})')
                if dists:
                    for a, b, d in dists:
                        print(f'  |{a.strip("/")}↔{b.strip("/")}| = {d:.3f} m')
                break

    except KeyboardInterrupt:
        print('\nInterrupted by user.')
    finally:
        stop = Twist()
        for driver in drivers:
            driver.cmd_pub.publish(stop)
            driver.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()