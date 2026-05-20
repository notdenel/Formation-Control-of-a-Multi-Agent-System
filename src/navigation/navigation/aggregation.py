#!/usr/bin/env python3
"""
Multi-robot aggregation using APF + odometry feedback.

Architecture (robot-local deployment):
  - odom_bridge brings peer /robotY/odom and /robotZ/odom into this robot's
    private domain via domain_bridge.
  - This node discovers all live robots by verifying actual odom message flow
    (not just topic existence — avoids ghost topics from idle bridge endpoints).
  - One RobotDriver is created per discovered namespace.  When running on a
    robot (robot_name param set), only the own driver publishes meaningful
    cmd_vel (peers' cmd_vel publishers go to no subscriber — harmless).
  - No cross-domain ready handshake needed: control starts as soon as all
    peers' PeerState.ready flags are set by the first arriving odom message.

Usage:
    ros2 run navigation aggregation
    # or via real_robot.launch.py (passes robot_name param automatically)
"""

import os
import threading
import math
import re

import rclpy
from rclpy.node import Node
from rclpy.executors import MultiThreadedExecutor
from nav_msgs.msg import Odometry
from geometry_msgs.msg import Twist


# ── APF gains ─────────────────────────────────────────────────────────────────
G_A = 10.0   # attraction gain  (toward peer)
G_R = 0.5    # repulsion gain   (away from peer at close range)

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
    """Lightweight thread-safe position store for one robot namespace."""
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
    Scans the ROS graph for active /robotX/odom topics, then verifies
    liveness by waiting for at least one real message on each candidate.
    Ghost topics from idle domain_bridge endpoints are filtered out because
    their DDS publisher has no upstream data source and never sends messages.
    """
    ODOM_PATTERN = re.compile(r'^(/robot\w+)/odom$')

    def __init__(self):
        super().__init__('aggregation_discovery')

    def discover(self, timeout_sec: float = 5.0) -> list[str]:
        """Return sorted list of namespaces whose /robotX/odom is live."""

        # Step 1: wait for candidate topic names to appear in the graph.
        deadline = self.get_clock().now().nanoseconds * 1e-9 + timeout_sec
        candidates: list[str] = []
        while self.get_clock().now().nanoseconds * 1e-9 < deadline:
            topics = self.get_topic_names_and_types()
            candidates = sorted({
                m.group(1)
                for topic, _ in topics
                if (m := self.ODOM_PATTERN.match(topic))
            })
            if candidates:
                break
            rclpy.spin_once(self, timeout_sec=0.2)

        if not candidates:
            self.get_logger().warn('[discovery] No /robotX/odom topics found.')
            return []

        # Step 2: verify liveness — ghost bridge endpoints advertise a publisher
        # but never emit messages.  Subscribe to each candidate and wait up to
        # 3 s for a real message before accepting the namespace.
        live: set[str] = set()
        lock = threading.Lock()

        subs = []
        for ns in candidates:
            def _cb(msg, ns=ns):
                with lock:
                    live.add(ns)
            subs.append(
                self.create_subscription(Odometry, f'{ns}/odom', _cb, 10))

        liveness_deadline = self.get_clock().now().nanoseconds * 1e-9 + 3.0
        while self.get_clock().now().nanoseconds * 1e-9 < liveness_deadline:
            rclpy.spin_once(self, timeout_sec=0.1)
            with lock:
                if live == set(candidates):
                    break   # all candidates confirmed live

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
    Controls one robot namespace.
    Peers are injected as PeerState objects after discovery.
    Control starts as soon as every peer's PeerState.ready flag is True
    (set on first odom message) — no cross-domain handshake needed.

    Implements: J_i(x) = Σ_{j≠i} [ G_A * error_ij * (-direction_ij) ]
    where error_ij = distance_ij - GOAL_TOLERANCE
    """

    def __init__(self, namespace: str):
        super().__init__(f'{namespace.strip("/")}_driver')

        self.namespace = namespace
        self.peers: list[PeerState] = []   # injected via add_peer()

        self._pos_lock = threading.Lock()
        self._pos: Vec2 | None = None

        self.current_yaw: float | None = None
        self.start_yaw:   float | None = None
        self.odom_ready = False
        self.done       = False

        self.cmd_pub = self.create_publisher(
            Twist, f'{namespace}/controller/cmd_vel', 10)

        self.create_timer(0.05, self._control_loop)
        self.get_logger().info(f'[{namespace}] Driver initialised.')

    def add_peer(self, peer: PeerState) -> None:
        self.peers.append(peer)

    def get_position(self) -> 'Vec2 | None':
        with self._pos_lock:
            return self._pos

    def _odom_cb(self, msg: Odometry) -> None:
        pose = msg.pose.pose
        with self._pos_lock:
            self._pos = Vec2(pose.position.x, pose.position.y)
        self.current_yaw = yaw_from_quaternion(pose.orientation)
        self.odom_ready  = True
        if self.start_yaw is None:
            self.start_yaw = self.current_yaw

    def _control_loop(self) -> None:
        if self.done or not self.odom_ready:
            return
        # Wait until every peer has sent at least one odom message.
        if not all(p.ready for p in self.peers):
            return
        if self.start_yaw is None:
            return

        pos_self = self.get_position()
        if pos_self is None:
            return

        # ── J_i(x) = Σ_{j≠i} [ G_A * error_ij * (-direction_ij) ] ──────────
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
            error     = distance - GOAL_TOLERANCE
            f_total   = f_total + (-direction) * G_A * error

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

        LINEAR_SPEED = 0.3
        world_vel    = f_total / f_norm * LINEAR_SPEED

        # ── World → body-frame ────────────────────────────────────────────────
        c = math.cos(self.current_yaw)
        s = math.sin(self.current_yaw)

        local_x =  c * world_vel.x + s * world_vel.y
        local_y = -s * world_vel.x + c * world_vel.y

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

    # ── 1. Discover live robots ───────────────────────────────────────────────
    discovery = DiscoveryNode()
    namespaces = discovery.discover(timeout_sec=5.0)
    discovery.destroy_node()

    if len(namespaces) < 1:
        print('[aggregation] No live robots found. Aborting.')
        rclpy.shutdown()
        return

    if len(namespaces) == 1:
        ns = namespaces[0]
        print(f'[aggregation] Only 1 robot found ({ns}). Running cmd_vel smoke test.')
        smoke = rclpy.create_node('aggregation_smoke')
        pub   = smoke.create_publisher(Twist, f'{ns}/controller/cmd_vel', 10)

        def smoke_pub():
            t = Twist()
            t.linear.x  = 0.1
            t.linear.y  = 0.1
            t.angular.z = 0.2
            pub.publish(t)

        smoke.create_timer(0.1, smoke_pub)
        try:
            rclpy.spin(smoke)
        except KeyboardInterrupt:
            stop = Twist()
            for _ in range(10):
                pub.publish(stop)
                rclpy.spin_once(smoke, timeout_sec=0.05)
        finally:
            smoke.destroy_node()
            rclpy.shutdown()
        return

    print(f'\nStarting aggregation for: {" ↔ ".join(namespaces)}\n'
          f'Equilibrium distance: {GOAL_TOLERANCE:.3f} m\n')

    # ── 2. Build shared PeerState map ─────────────────────────────────────────
    peer_states: dict[str, PeerState] = {ns: PeerState(ns) for ns in namespaces}

    # ── 3. Build one RobotDriver per namespace ────────────────────────────────
    drivers: list[RobotDriver] = []
    for ns in namespaces:
        driver = RobotDriver(ns)
        for other_ns, state in peer_states.items():
            if other_ns != ns:
                driver.add_peer(state)
        drivers.append(driver)

    # ── 4. Wire odom → PeerState (driver also updates shared store) ───────────
    for driver in drivers:
        state = peer_states[driver.namespace]
        original_cb = driver._odom_cb

        def make_cb(orig, s):
            def cb(msg):
                orig(msg)
                s.update(msg.pose.pose.position.x, msg.pose.pose.position.y)
            return cb

        driver._odom_cb = make_cb(original_cb, state)
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
                print('\nAll robots aggregated.')
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
            for _ in range(6):
                driver.cmd_pub.publish(stop)
                executor.spin_once(timeout_sec=0.05)
        for driver in drivers:
            driver.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
