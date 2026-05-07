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
import math
import sys


# ── Tunable parameters ────────────────────────────────────────────────────────
LINEAR_SPEED   = 0.2   # m/s – max speed along dominant axis
GOAL_TOLERANCE = 0.05  # m   – stop when this close to the goal
# ─────────────────────────────────────────────────────────────────────────────


def yaw_from_quaternion(q):
    """Extract yaw (heading) from a geometry_msgs/Quaternion."""
    siny_cosp = 2.0 * (q.w * q.z + q.x * q.y)
    cosy_cosp = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
    return math.atan2(siny_cosp, cosy_cosp)


class RobotDriver(Node):
    """
    Controls a single robot namespace.
    Subscribes to /robotX/odom and publishes to /robotX/cmd_vel.
    Strafes the robot to (goal_x, goal_y) without changing heading.
    """

    def __init__(self, namespace: str, goal_x: float, goal_y: float):
        super().__init__(f'{namespace.strip("/")}_driver')

        self.namespace   = namespace
        self.goal_x      = goal_x
        self.goal_y      = goal_y

        # Odometry state
        self.current_x   = None
        self.current_y   = None
        self.current_yaw = None
        self.odom_ready  = False

        # Done flag
        self.done = False

        # Publisher & subscriber
        self.cmd_pub = self.create_publisher(Twist, f'{namespace}/cmd_vel', 10)
        self.odom_sub = self.create_subscription(
            Odometry, f'{namespace}/odom', self._odom_callback, 10)

        # Control loop at 20 Hz
        self.timer = self.create_timer(0.05, self._control_loop)

        self.get_logger().info(
            f'[{namespace}] Driver started. Goal: ({goal_x:.3f}, {goal_y:.3f})')

    # ── Callbacks ─────────────────────────────────────────────────────────────

    def _odom_callback(self, msg: Odometry):
        pose = msg.pose.pose
        self.current_x   = pose.position.x
        self.current_y   = pose.position.y
        self.current_yaw = yaw_from_quaternion(pose.orientation)
        self.odom_ready  = True

    # ── Control loop ──────────────────────────────────────────────────────────

    def _control_loop(self):
        if self.done or not self.odom_ready:
            return

        dx = self.goal_x - self.current_x
        dy = self.goal_y - self.current_y
        distance = math.hypot(dx, dy)

        twist = Twist()

        if distance < GOAL_TOLERANCE:
            # ── Goal reached ──
            self.cmd_pub.publish(twist)   # zero velocity
            self.done = True
            self.get_logger().info(
                f'[{self.namespace}] Goal reached! '
                f'Final pos: ({self.current_x:.3f}, {self.current_y:.3f})')
            return

        # ── Holonomic strafe: world-frame error → robot-local-frame velocities ──
        # Rotate (dx, dy) from the odom/world frame into the robot's body frame
        # using the current yaw. angular.z stays 0 — heading never changes.
        cos_yaw = math.cos(self.current_yaw)
        sin_yaw = math.sin(self.current_yaw)

        local_x =  cos_yaw * dx + sin_yaw * dy   # forward/back in robot frame
        local_y = -sin_yaw * dx + cos_yaw * dy   # left/right strafe in robot frame

        # Scale so the dominant axis reaches LINEAR_SPEED (preserves direction)
        max_component = max(abs(local_x), abs(local_y))
        scale = LINEAR_SPEED / max_component

        twist.linear.x = scale * local_x
        twist.linear.y = scale * local_y
        # twist.angular.z = 0.0  (default — heading never changes)

        self.cmd_pub.publish(twist)
        self.get_logger().info(
            f'[{self.namespace}] dist={distance:.3f} m  '
            f'vx={twist.linear.x:.3f}  vy={twist.linear.y:.3f}',
            throttle_duration_sec=0.5)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    # ── Parse goal coordinate from CLI args ──────────────────────────────────
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

    robot1 = RobotDriver('/robot1', goal_x, goal_y)
    robot3 = RobotDriver('/robot3', goal_x, goal_y)

    executor = MultiThreadedExecutor(num_threads=4)
    executor.add_node(robot1)
    executor.add_node(robot3)

    try:
        while rclpy.ok():
            executor.spin_once(timeout_sec=0.05)
            if robot1.done and robot3.done:
                print('\nBoth robots have reached their goal. Shutting down.')
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