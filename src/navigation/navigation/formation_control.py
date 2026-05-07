#!/usr/bin/env python3
"""
Drive robot1 and robot3 to a user-specified (x, y) coordinate simultaneously,
using odometry feedback (/robotX/odom) to know when the target distance is reached.
Robots use mecanum wheels and strafe directly without changing heading.

Usage:
    ros2 run navigation aggregation <x> <y>
"""

import rclpy
from rclpy.node import Node
from rclpy.executors import MultiThreadedExecutor
from nav_msgs.msg import Odometry
from geometry_msgs.msg import Twist
from std_msgs.msg import Bool
import math
import sys


LINEAR_SPEED   = 0.2   # m/s – max speed along dominant axis
GOAL_TOLERANCE = 0.05  # m   – stop when this close to the goal

G_A = 0.2
G_R = 0.1

class Vec2:
    """Minimal 2-D vector supporting attribute access and arithmetic."""

    def __init__(self, x: float = 0.0, y: float = 0.0):
        self.x = x
        self.y = y

    def __add__(self, other: 'Vec2') -> 'Vec2':
        return Vec2(self.x + other.x, self.y + other.y)

    def __sub__(self, other: 'Vec2') -> 'Vec2':
        return Vec2(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar: float) -> 'Vec2':
        return Vec2(self.x * scalar, self.y * scalar)

    def __rmul__(self, scalar: float) -> 'Vec2':
        return self.__mul__(scalar)

    def __truediv__(self, scalar: float) -> 'Vec2':
        return Vec2(self.x / scalar, self.y / scalar)

    def __repr__(self) -> str:
        return f'Vec2({self.x:.3f}, {self.y:.3f})'

    def norm(self) -> float:
        return math.hypot(self.x, self.y)

    def normalized(self) -> 'Vec2':
        n = self.norm()
        return self / n if n > 1e-9 else Vec2(0.0, 0.0)


def yaw_from_quaternion(q):
    """Extract yaw (heading) from a geometry_msgs/Quaternion."""
    siny_cosp = 2.0 * (q.w * q.z + q.x * q.y)
    cosy_cosp = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
    return math.atan2(siny_cosp, cosy_cosp)


class RobotDriver(Node):
    """
    Controls a single robot namespace.
    Subscribes to /robotX/odom and publishes to /robotX/cmd_vel.
    Strafes the robot toward its peer using inter-agent spring forces.
    Waits for all peers to be ready before moving.
    """

    def __init__(self, namespace: str, all_namespaces: list[str], goal_x: float, goal_y: float):
        super().__init__(f'{namespace.strip("/")}_driver')

        self.namespace = namespace
        self.goal_x    = goal_x
        self.goal_y    = goal_y

        # Peer robot
        self.peer: 'RobotDriver | None' = None

        # Odometry state
        self.pos: Vec2 | None = None
        self.current_yaw      = None
        self.odom_ready       = False

        # Ready-sync barrier
        self.ready_peers  = set()
        self.all_namespaces = set(all_namespaces) - {namespace}
        self.all_ready    = False

        # Done flag
        self.done = False

        # Publishers & subscribers
        self.cmd_pub  = self.create_publisher(Twist, f'{namespace}/cmd_vel', 10)
        self.ready_pub = self.create_publisher(Bool,  f'{namespace}/ready',   10)

        self.odom_sub = self.create_subscription(
            Odometry, f'{namespace}/odom', self._odom_callback, 10)

        for ns in all_namespaces:
            if ns != namespace:
                self.create_subscription(
                    Bool, f'{ns}/ready',
                    lambda msg, ns=ns: self._ready_callback(ns),
                    10)

        # Control loop at 20 Hz
        self.timer = self.create_timer(0.05, self._control_loop)

        self.get_logger().info(
            f'[{namespace}] Driver started. Goal: ({goal_x:.3f}, {goal_y:.3f})')

    def set_peer(self, peer: 'RobotDriver'):
        """Wire up the other robot so _control_loop can read its position."""
        self.peer = peer

    def _odom_callback(self, msg: Odometry):
        pose             = msg.pose.pose
        self.pos         = Vec2(pose.position.x, pose.position.y)
        self.current_yaw = yaw_from_quaternion(pose.orientation)
        self.odom_ready  = True
        # Broadcast readiness on every odom tick until all peers are ready
        if not self.all_ready:
            self.ready_pub.publish(Bool(data=True))

    def _ready_callback(self, peer_ns: str):
        self.ready_peers.add(peer_ns)
        if self.all_namespaces.issubset(self.ready_peers):
            self.all_ready = True
            self.get_logger().info(
                f'[{self.namespace}] All peers ready — starting!')

    def get_position(self) -> 'Vec2 | None':
        """Return current position as a Vec2, or None if not yet received."""
        return self.pos

    # ── Control loop ──────────────────────────────────────────────────────────

    def _control_loop(self):
        if self.done or not self.odom_ready or not self.all_ready:
            return

        if self.peer is None or not self.peer.odom_ready:
            return

        pos_self = self.pos
        pos_peer = self.peer.pos

        # ── Inter-agent spring force ───────────────────────────────────────
        delta    = pos_self - pos_peer
        distance = delta.norm()

        force = (G_A - G_R) * delta
        vx_sum = force.x
        vy_sum = force.y

        twist = Twist()

        if distance < GOAL_TOLERANCE:
            self.cmd_pub.publish(twist)   # zero velocity
            self.done = True
            self.get_logger().info(
                f'[{self.namespace}] Goal reached! '
                f'Final pos: ({pos_self.x:.3f}, {pos_self.y:.3f})')
            return

        # ── Holonomic strafe: world-frame velocity → robot-local-frame ────
        cos_yaw = math.cos(self.current_yaw)
        sin_yaw = math.sin(self.current_yaw)

        local_x =  cos_yaw * vx_sum + sin_yaw * vy_sum
        local_y = -sin_yaw * vx_sum + cos_yaw * vy_sum

        max_component = max(abs(local_x), abs(local_y), 1e-6)
        scale = LINEAR_SPEED / max_component

        twist.linear.x = scale * local_x
        twist.linear.y = scale * local_y

        self.cmd_pub.publish(twist)
        self.get_logger().info(
            f'[{self.namespace}] dist={distance:.3f} m  '
            f'vx={twist.linear.x:.3f}  vy={twist.linear.y:.3f}',
            throttle_duration_sec=0.5)


def compute_inter_agent_distance(robot1: RobotDriver, robot3: RobotDriver) -> float | None:
    """
    Compute Euclidean distance between robot1 and robot3 in the odom frame.
    """
    pos1 = robot1.get_position()
    pos3 = robot3.get_position()

    if pos1 is None or pos3 is None:
        return None

    return (pos3 - pos1).norm()


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) == 3:
        try:
            goal_x = float(sys.argv[1])
            goal_y = float(sys.argv[2])
        except ValueError:
            print('Usage: ros2 run navigation aggregation <x> <y>')
            sys.exit(1)
    else:
        try:
            goal_x = float(input('Enter goal X (meters, relative to odom origin): '))
            goal_y = float(input('Enter goal Y (meters, relative to odom origin): '))
        except (ValueError, EOFError):
            print('Invalid input. Exiting.')
            sys.exit(1)

    print(f'\nDriving both robots to ({goal_x:.3f}, {goal_y:.3f}) …\n')

    rclpy.init()

    namespaces = ['/robot1', '/robot3']
    robot1 = RobotDriver('/robot1', namespaces, goal_x, goal_y)
    robot3 = RobotDriver('/robot3', namespaces, goal_x, goal_y)

    # ── Wire peers BEFORE the executor starts spinning ────────────────────────
    robot1.set_peer(robot3)
    robot3.set_peer(robot1)

    executor = MultiThreadedExecutor(num_threads=4)
    executor.add_node(robot1)
    executor.add_node(robot3)

    last_distance_log = 0.0

    try:
        while rclpy.ok():
            executor.spin_once(timeout_sec=0.05)

            pos1 = robot1.get_position()
            pos3 = robot3.get_position()
            inter_dist = compute_inter_agent_distance(robot1, robot3)

            now = robot1.get_clock().now().nanoseconds * 1e-9

            if inter_dist is not None and (now - last_distance_log) >= 1.0:
                print(
                    f'[distance]  '
                    f'robot1=({pos1.x:.3f}, {pos1.y:.3f})  '
                    f'robot3=({pos3.x:.3f}, {pos3.y:.3f})  '
                    f'|Δ|={inter_dist:.3f} m'
                )
                last_distance_log = now

            if robot1.done and robot3.done:
                pos1 = robot1.get_position()
                pos3 = robot3.get_position()
                final_dist = compute_inter_agent_distance(robot1, robot3)
                print(
                    f'\nBoth robots reached goal.\n'
                    f'  robot1 final pos : ({pos1.x:.3f}, {pos1.y:.3f})\n'
                    f'  robot3 final pos : ({pos3.x:.3f}, {pos3.y:.3f})\n'
                    f'  Final inter-agent distance: {final_dist:.3f} m'
                )
                break

    except KeyboardInterrupt:
        print('\nInterrupted by user.')
    finally:
        stop = Twist()
        robot1.cmd_pub.publish(stop)
        robot3.cmd_pub.publish(stop)
        robot1.destroy_node()
        robot3.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()