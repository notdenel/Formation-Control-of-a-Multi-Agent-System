#!/usr/bin/env python3
# encoding: utf-8
import os
import rclpy
from rclpy.node import Node
from std_srvs.srv import Trigger
from slam_toolbox.srv import SaveMap

MAPS_DIR = os.path.expanduser('~/ros2_ws/src/slam/maps')

class MapSaveNode(Node):
    def __init__(self, name):
        super().__init__(name)
        self.create_service(SaveMap, '/slam_toolbox/save_map', self.save_srv_callback)
        self.create_service(Trigger, '~/init_finish', self.get_node_state)
        self.get_logger().info('\033[1;32m%s\033[0m' % 'map_save node started')

    def get_node_state(self, request, response):
        response.success = True
        return response

    def save_srv_callback(self, request, response):
        self.get_logger().info('\033[1;32m%s\033[0m' % 'saving map to ' + MAPS_DIR)
        os.makedirs(MAPS_DIR, exist_ok=True)
        map_path = os.path.join(MAPS_DIR, 'map_01')
        os.system(
            f'ros2 run nav2_map_server map_saver_cli -f "{map_path}"'
            ' --ros-args -p map_subscribe_transient_local:=true'
        )
        return response

def main():
    rclpy.init()
    node = MapSaveNode('map_save_node')
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
