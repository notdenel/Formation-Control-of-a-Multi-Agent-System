#!/usr/bin/env python3
import yaml
import numpy as np
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu


class ApplyCalib(Node):
    def __init__(self):
        super().__init__('imu_calib')
        self.declare_parameter('calib_file', '')
        calib_file = self.get_parameter('calib_file').get_parameter_value().string_value
        if not calib_file:
            raise RuntimeError('calib_file parameter is required')

        with open(calib_file, 'r') as f:
            data = yaml.safe_load(f)

        sm_flat = data['SM']
        bias = data['bias']
        self._gyro_bias = np.array(data.get('gyro_bias', [0.0, 0.0, 0.0]), dtype=float)
        self._SM = np.array(sm_flat, dtype=float).reshape(3, 3)
        self._bias = np.array(bias, dtype=float)

        self._pub = self.create_publisher(Imu, 'corrected', 10)
        self.create_subscription(Imu, 'raw', self._callback, 10)

    def _callback(self, msg: Imu):
        raw = np.array([
            msg.linear_acceleration.x,
            msg.linear_acceleration.y,
            msg.linear_acceleration.z,
        ])
        corrected = self._SM @ (raw - self._bias)
        
        raw_gyro = np.array([
            msg.angular_velocity.x,
            msg.angular_velocity.y,
            msg.angular_velocity.z,
        ])
        corrected_gyro = raw_gyro - self._gyro_bias

        out = Imu()
        out.header = msg.header
        out.orientation = msg.orientation
        out.orientation_covariance = msg.orientation_covariance
        out.angular_velocity.x = corrected_gyro[0]
        out.angular_velocity.y = corrected_gyro[1]
        out.angular_velocity.z = corrected_gyro[2]
        out.angular_velocity_covariance = msg.angular_velocity_covariance
        out.linear_acceleration.x = corrected[0]
        out.linear_acceleration.y = corrected[1]
        out.linear_acceleration.z = corrected[2]
        out.linear_acceleration_covariance = msg.linear_acceleration_covariance
        self._pub.publish(out)


def main():
    rclpy.init()
    node = ApplyCalib()
    rclpy.spin(node)
    rclpy.shutdown()


if __name__ == '__main__':
    main()
