#!/usr/bin/env python3
import os
import rclpy
from rclpy.node import Node
from std_srvs.srv import Trigger

MAPS_DIR = os.path.expanduser('~/ros2_ws/src/slam/maps')


class MapSaveNode(Node):
    def __init__(self):
        super().__init__('map_save_node')

        # The map topic that slam_toolbox publishes is RELATIVE in our setup,
        # so under PushRosNamespace(robot1) it becomes /robot1/map. We can ask
        # rclpy for our own effective namespace and build the absolute topic
        # name from there.
        ns = self.get_namespace().rstrip('/')   # '' or '/robot1'
        self._map_topic          = f'{ns}/map'           if ns else '/map'
        self._map_metadata_topic = f'{ns}/map_metadata'  if ns else '/map_metadata'

        self.create_service(Trigger, '~/save_map',    self.save_srv_callback)
        self.create_service(Trigger, '~/init_finish', self.get_node_state)

        self.get_logger().info(
            f'map_save_node ready (subscribed map topic: {self._map_topic})'
        )
        self.get_logger().info(
            f'To save the map call: '
            f'ros2 service call {ns}/map_save_node/save_map std_srvs/srv/Trigger'
        )

    def get_node_state(self, request, response):
        response.success = True
        return response

    def save_srv_callback(self, request, response):
        os.makedirs(MAPS_DIR, exist_ok=True)
        map_path = os.path.join(MAPS_DIR, 'map_01')
        self.get_logger().info(f'Saving map -> {map_path}')

        # Critical flags:
        #   map_subscribe_transient_local=true  -- slam_toolbox publishes /map
        #                                          with TRANSIENT_LOCAL durability,
        #                                          so the subscriber must match.
        #   save_map_timeout=10.0               -- 2 s default is unreliable on a Pi.
        # Remap /map and /map_metadata to the namespaced topics resolved above.
        cmd = (
            f'ros2 run nav2_map_server map_saver_cli '
            f'-f "{map_path}" '
            f'--ros-args '
            f'-p map_subscribe_transient_local:=true '
            f'-p save_map_timeout:=10.0 '
            f'-r /map:={self._map_topic} '
            f'-r /map_metadata:={self._map_metadata_topic}'
        )
        self.get_logger().info(f'Running: {cmd}')
        ret = os.system(cmd)
        response.success = (ret == 0)
        response.message = (
            f'Map saved to {map_path}' if ret == 0
            else f'Map save failed (exit code {ret})'
        )
        self.get_logger().info(response.message)
        return response


def main():
    rclpy.init()
    node = MapSaveNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()