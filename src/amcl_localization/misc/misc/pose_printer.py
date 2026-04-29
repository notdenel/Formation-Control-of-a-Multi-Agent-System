"""
pose_printer.py
===============
Subscribes to /amcl_pose and prints x, y, yaw at 2 Hz.

This is the canonical way to read the robot's pose (in the map frame)
when you're using AMCL on a static map. /amcl_pose is a
geometry_msgs/PoseWithCovarianceStamped — it's published every time
AMCL updates (typically when the robot moves more than update_min_d /
update_min_a, set in amcl_params.yaml).

If you need a continuous stream regardless of AMCL update rate, look up
the map -> base_footprint TF instead (commented example at the bottom).
"""

import math
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseWithCovarianceStamped


def quat_to_yaw(q):
    """Convert geometry_msgs/Quaternion -> yaw (radians)."""
    siny_cosp = 2.0 * (q.w * q.z + q.x * q.y)
    cosy_cosp = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
    return math.atan2(siny_cosp, cosy_cosp)


class PosePrinter(Node):
    def __init__(self):
        super().__init__('pose_printer')
        self.last_pose = None
        self.create_subscription(
            PoseWithCovarianceStamped, '/amcl_pose', self.cb, 10)
        self.create_timer(0.5, self.tick)
        self.get_logger().info(
            'pose_printer up — waiting for /amcl_pose '
            '(set initial pose in RViz if needed)')

    def cb(self, msg: PoseWithCovarianceStamped):
        self.last_pose = msg

    def tick(self):
        if self.last_pose is None:
            return
        p = self.last_pose.pose.pose.position
        yaw = quat_to_yaw(self.last_pose.pose.pose.orientation)
        cov = self.last_pose.pose.covariance
        # cov is a 6x6 row-major flat list: indices 0 (xx), 7 (yy), 35 (yawyaw)
        self.get_logger().info(
            f'x={p.x:+.3f} m  y={p.y:+.3f} m  yaw={math.degrees(yaw):+6.1f}°  '
            f'(σx={math.sqrt(max(cov[0],0)):.3f}, '
            f'σy={math.sqrt(max(cov[7],0)):.3f})'
        )


def main():
    rclpy.init()
    node = PosePrinter()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()


# ──────────────────────────────────────────────────────────────────────────
# Alternative: continuous pose via TF lookup (not bound to AMCL update rate)
# ──────────────────────────────────────────────────────────────────────────
# from tf2_ros import Buffer, TransformListener
# from rclpy.duration import Duration
#
# class PoseFromTF(Node):
#     def __init__(self):
#         super().__init__('pose_from_tf')
#         self.buf = Buffer()
#         self.tl  = TransformListener(self.buf, self)
#         self.create_timer(0.1, self.tick)  # 10 Hz
#
#     def tick(self):
#         try:
#             t = self.buf.lookup_transform(
#                 'map', 'base_footprint', rclpy.time.Time(),
#                 timeout=Duration(seconds=0.1))
#         except Exception:
#             return
#         x = t.transform.translation.x
#         y = t.transform.translation.y
#         self.get_logger().info(f'x={x:+.3f} y={y:+.3f}')
