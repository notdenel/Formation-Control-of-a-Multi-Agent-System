#!/usr/bin/env python3
import math

import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from geometry_msgs.msg import Twist


def _yaw_from_quaternion(q) -> float:
    siny_cosp = 2.0 * (q.w * q.z + q.x * q.y)
    cosy_cosp = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
    return math.atan2(siny_cosp, cosy_cosp)


class GoToGoal(Node):
    """
    Drive a mecanum robot from its current odom position to a goal (x, y).

    Computes the straight-line vector once the first odom message arrives,
    then continuously publishes body-frame Twist commands with proportional
    speed (capped at max_speed) until within goal_tolerance of the target.
    """

    def __init__(self):
        super().__init__('goto_goal')

        self.declare_parameter('goal_x', 0.0)
        self.declare_parameter('goal_y', 0.0)
        self.declare_parameter('max_speed', 0.25)        # m/s
        self.declare_parameter('goal_tolerance', 0.20)   # metres
        self.declare_parameter('ga', 1.0)                # proportional gain
        self.declare_parameter('odom_topic', '/odom')
        self.declare_parameter('cmd_vel_topic', 'controller/cmd_vel')

        odom_topic = self.get_parameter('odom_topic').value
        cmd_vel_topic = self.get_parameter('cmd_vel_topic').value

        self._pub = self.create_publisher(Twist, cmd_vel_topic, 1)
        self._sub = self.create_subscription(Odometry, odom_topic, self._odom_cb, 10)

        self._pos_x: float | None = None
        self._pos_y: float | None = None
        self._yaw: float = 0.0
        self._done = False

        self.create_timer(0.05, self._step)   # 20 Hz control loop

        gx = self.get_parameter('goal_x').value
        gy = self.get_parameter('goal_y').value
        self.get_logger().info(
            f'goto_goal ready  →  goal ({gx:.3f}, {gy:.3f})  '
            f'odom: {odom_topic}  cmd_vel: {cmd_vel_topic}'
        )

    # ------------------------------------------------------------------ odom
    def _odom_cb(self, msg: Odometry) -> None:
        self._pos_x = msg.pose.pose.position.x
        self._pos_y = msg.pose.pose.position.y
        self._yaw = _yaw_from_quaternion(msg.pose.pose.orientation)

    # ----------------------------------------------------------- control loop
    def _step(self) -> None:
        if self._pos_x is None:
            return

        # Keep asserting zero so the motor controller never runs on stale velocity.
        if self._done:
            self._stop()
            return

        goal_x = self.get_parameter('goal_x').value
        goal_y = self.get_parameter('goal_y').value
        max_spd = self.get_parameter('max_speed').value
        tol = self.get_parameter('goal_tolerance').value
        ga = self.get_parameter('ga').value

        #error + dist
        dx = goal_x - self._pos_x
        dy = goal_y - self._pos_y
        dist = math.hypot(dx, dy)

        if dist < tol:
            self._stop()
            self._done = True
            self.get_logger().info(
                f'Goal reached!  pos=({self._pos_x:.3f}, {self._pos_y:.3f})  err={dist:.4f} m'
            )
            return

        # Proportional speed, capped
        speed = min(ga * dist, max_spd)

        # Unit vector toward goal in odom frame
        ux = dx / dist
        uy = dy / dist

        # Rotate into robot body frame using current yaw
        cos_y = math.cos(self._yaw)
        sin_y = math.sin(self._yaw)
        vx_body = ux * cos_y + uy * sin_y
        vy_body = -ux * sin_y + uy * cos_y

        twist = Twist()
        twist.linear.x = vx_body * speed
        twist.linear.y = vy_body * speed   # mecanum strafe
        self._pub.publish(twist)

    def _stop(self) -> None:
        self._pub.publish(Twist())


def main(args=None):
    rclpy.init(args=args)
    node = GoToGoal()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node._stop()
        node.destroy_node()
        rclpy.shutdown()
