#!/usr/bin/env python3
"""
pose_aggregator.py
==================
Subscribes to /robotX/amcl_pose for each robot and publishes a combined
/global_robot_states (geometry_msgs/PoseArray, frame_id: map) at 5 Hz.

Topics subscribed:
  /robot1/amcl_pose  (geometry_msgs/PoseWithCovarianceStamped)
  /robot2/amcl_pose
  /robot3/amcl_pose

Topics published:
  /global_robot_states  (geometry_msgs/PoseArray, frame_id=map)
    poses[0] = robot1, poses[1] = robot2, poses[2] = robot3
    Missing poses have position.z = -1.0 to signal "not yet localised".
"""

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, DurabilityPolicy, ReliabilityPolicy, HistoryPolicy
from geometry_msgs.msg import PoseArray, PoseWithCovarianceStamped, Pose


AMCL_QOS = QoSProfile(
    depth=1,
    reliability=ReliabilityPolicy.RELIABLE,
    durability=DurabilityPolicy.TRANSIENT_LOCAL,
    history=HistoryPolicy.KEEP_LAST,
)


class PoseAggregator(Node):
    def __init__(self):
        super().__init__('pose_aggregator')

        self.declare_parameter('robot_names', ['robot1', 'robot2', 'robot3'])
        self.robot_names = (
            self.get_parameter('robot_names').get_parameter_value().string_array_value
        )

        self._poses: dict[str, Pose] = {}
        self._received: dict[str, bool] = {n: False for n in self.robot_names}

        for name in self.robot_names:
            self.create_subscription(
                PoseWithCovarianceStamped,
                f'/{name}/amcl_pose',
                lambda msg, n=name: self._amcl_cb(msg, n),
                AMCL_QOS,
            )

        self._pub = self.create_publisher(PoseArray, '/global_robot_states', 10)
        self.create_timer(0.2, self._publish)

        self.get_logger().info(
            f'pose_aggregator ready — tracking: {list(self.robot_names)}'
        )

    def _amcl_cb(self, msg: PoseWithCovarianceStamped, robot_name: str) -> None:
        self._poses[robot_name] = msg.pose.pose
        if not self._received[robot_name]:
            self._received[robot_name] = True
            self.get_logger().info(f'First pose received from {robot_name}')

    def _publish(self) -> None:
        msg = PoseArray()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'map'

        for name in self.robot_names:
            if name in self._poses:
                msg.poses.append(self._poses[name])
            else:
                sentinel = Pose()
                sentinel.position.z = -1.0  # signals "not yet localised"
                msg.poses.append(sentinel)

        self._pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = PoseAggregator()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
