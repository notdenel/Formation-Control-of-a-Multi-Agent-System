#!/usr/bin/env python3
# encoding: utf-8
import os
import rclpy
from rclpy.node import Node
from std_srvs.srv import Trigger

MAPS_DIR = os.path.expanduser('~/ros2_ws/src/slam/maps')


class MapSaveNode(Node):
    def __init__(self, name):
        super().__init__(name)
        # Unique service name — does not conflict with slam_toolbox's own service.
        self.create_service(Trigger, '~/save_map', self.save_srv_callback)
        self.create_service(Trigger, '~/init_finish', self.get_node_state)
        self.get_logger().info('\033[1;32m%s\033[0m' % 'map_save node started')
        self.get_logger().info(
            '\033[1;32mTo save the map call: '
            'ros2 service call /map_save_node/save_map std_srvs/srv/Trigger\033[0m'
        )

    def get_node_state(self, request, response):
        response.success = True
        return response

    def save_srv_callback(self, request, response):
        self.get_logger().info('\033[1;32m%s\033[0m' % 'saving map to ' + MAPS_DIR)
        os.makedirs(MAPS_DIR, exist_ok=True)
        map_path = os.path.join(MAPS_DIR, 'map_01')
        # map_saver_cli subscribes to /map (transient_local QoS published by slam_toolbox)
        # and writes map_path.pgm + map_path.yaml
        ret = os.system(
            f'ros2 run nav2_map_server map_saver_cli -f "{map_path}"'
            ' --ros-args -p map_subscribe_transient_local:=true'
        )
        response.success = (ret == 0)
        response.message = (
            f'Map saved to {map_path}' if ret == 0
            else f'Map save failed (exit code {ret})'
        )
        self.get_logger().info('\033[1;32m%s\033[0m' % response.message)
        return response


def main():
    rclpy.init()
    node = MapSaveNode('map_save_node')
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
