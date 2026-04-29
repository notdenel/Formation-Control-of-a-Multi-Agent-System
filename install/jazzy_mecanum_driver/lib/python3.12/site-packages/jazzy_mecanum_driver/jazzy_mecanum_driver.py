#!/usr/bin/env python3
# encoding: utf-8
"""Single-file ROS 2 Jazzy mecanum drive node.

Consolidates the relevant pieces of the legacy ROS 2 Humble stack
(driver/controller/controller/mecanum.py and
driver/ros_robot_controller/ros_robot_controller/{ros_robot_controller_node.py,
ros_robot_controller_sdk.py}) into one rclpy node that:

  * subscribes to geometry_msgs/Twist on /cmd_vel,
  * applies mecanum inverse kinematics,
  * converts per-wheel linear speeds (m/s) to rotations-per-second,
  * sends them to the STM32 controller over serial using the original
    0xAA 0x55 framing protocol (PACKET_FUNC_MOTOR sub-command 0x01),
  * stops the wheels on command timeout and on shutdown.

If the pyserial port cannot be opened (no hardware, wrong device, etc.)
the node falls back to a simulation/dry-run mode and only logs the
commanded wheel rps values.

Package placement
-----------------
Drop this file into a ROS 2 Jazzy ament_python package, e.g.::

    my_robot_bringup/
    ├── my_robot_bringup/
    │   ├── __init__.py
    │   └── jazzy_mecanum_driver.py     <-- this file
    ├── package.xml
    ├── setup.cfg
    └── setup.py

Add a console_scripts entry in setup.py::

    entry_points={
        'console_scripts': [
            'jazzy_mecanum_driver = '
            'my_robot_bringup.jazzy_mecanum_driver:main',
        ],
    },

Build and run::

    colcon build --packages-select my_robot_bringup
    source install/setup.bash
    ros2 run my_robot_bringup jazzy_mecanum_driver

Or, without a package, just::

    python3 jazzy_mecanum_driver.py

Override parameters at runtime, e.g.::

    ros2 run my_robot_bringup jazzy_mecanum_driver --ros-args \
        -p wheelbase:=0.1368 -p track_width:=0.1410 \
        -p wheel_diameter:=0.065 -p serial_port:=/dev/rrc \
        -p dry_run:=false

Hardware assumptions (inferred from the legacy code)
----------------------------------------------------
  * 4-wheel mecanum chassis.
  * STM32 controller exposed at /dev/rrc, 1_000_000 baud, 8N1.
  * Motor IDs 1..4 with the layout
            x (forward)
        m1  ↑   m3
            |
        m2      m4
  * Legacy code applied per-wheel sign pattern [-1, -1, +1, +1]
    (front-left and rear-left inverted) before sending to the board;
    that is preserved here as the default ``motor_directions``.
  * Motor type defaults to JGB27 (0x02) and battery level to 0x1af4
    (Mecanum default), matching the legacy ros_robot_controller_node.
  * No custom message packages (ros_robot_controller_msgs) are required
    because we drive the board directly over serial in this single file.

If your robot diverges from these assumptions, override the relevant
ROS parameters --- nothing here is hard-coded.
"""

import math
import struct
import threading
import time
from typing import List, Optional

import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node
from rclpy.parameter import Parameter

try:
    import serial  # pyserial
except ImportError:  # pragma: no cover - serial is optional in dry-run
    serial = None


# ---------------------------------------------------------------------------
# Serial protocol constants (lifted from ros_robot_controller_sdk.py)
# ---------------------------------------------------------------------------

PACKET_FUNC_SYS = 0
PACKET_FUNC_MOTOR = 3

# CRC-8 table used by the STM32 firmware.
_CRC8_TABLE = [
    0, 94, 188, 226, 97, 63, 221, 131, 194, 156, 126, 32, 163, 253, 31, 65,
    157, 195, 33, 127, 252, 162, 64, 30, 95, 1, 227, 189, 62, 96, 130, 220,
    35, 125, 159, 193, 66, 28, 254, 160, 225, 191, 93, 3, 128, 222, 60, 98,
    190, 224, 2, 92, 223, 129, 99, 61, 124, 34, 192, 158, 29, 67, 161, 255,
    70, 24, 250, 164, 39, 121, 155, 197, 132, 218, 56, 102, 229, 187, 89, 7,
    219, 133, 103, 57, 186, 228, 6, 88, 25, 71, 165, 251, 120, 38, 196, 154,
    101, 59, 217, 135, 4, 90, 184, 230, 167, 249, 27, 69, 198, 152, 122, 36,
    248, 166, 68, 26, 153, 199, 37, 123, 58, 100, 134, 216, 91, 5, 231, 185,
    140, 210, 48, 110, 237, 179, 81, 15, 78, 16, 242, 172, 47, 113, 147, 205,
    17, 79, 173, 243, 112, 46, 204, 146, 211, 141, 111, 49, 178, 236, 14, 80,
    175, 241, 19, 77, 206, 144, 114, 44, 109, 51, 209, 143, 12, 82, 176, 238,
    50, 108, 142, 208, 83, 13, 239, 177, 240, 174, 76, 18, 145, 207, 45, 115,
    202, 148, 118, 40, 171, 245, 23, 73, 8, 86, 180, 234, 105, 55, 213, 139,
    87, 9, 235, 181, 54, 104, 138, 212, 149, 203, 41, 119, 244, 170, 72, 22,
    233, 183, 85, 11, 136, 214, 52, 106, 43, 117, 151, 201, 74, 20, 246, 168,
    116, 42, 200, 150, 21, 75, 169, 247, 182, 232, 10, 84, 215, 137, 107, 53,
]


def _crc8(data: bytes) -> int:
    check = 0
    for b in data:
        check = _CRC8_TABLE[check ^ b]
    return check & 0xFF


# ---------------------------------------------------------------------------
# Minimal Board wrapper -- only the bits we actually need to drive motors
# ---------------------------------------------------------------------------


class _BoardLink:
    """Thin serial link to the STM32 controller.

    Only implements the small subset of the legacy SDK that this node
    needs: ``set_motor_type``, ``set_battery_level``, and
    ``set_motor_speed``. If pyserial is missing or the port cannot be
    opened, ``connected`` stays ``False`` and every send becomes a
    no-op so the node can run in dry-run mode.
    """

    def __init__(self, device: str, baudrate: int, timeout: float):
        self.device = device
        self.baudrate = baudrate
        self.timeout = timeout
        self.port = None
        self.connected = False
        self._lock = threading.Lock()

    def open(self) -> Optional[str]:
        if serial is None:
            return "pyserial not installed"
        try:
            self.port = serial.Serial(None, self.baudrate, timeout=self.timeout)
            self.port.rts = False
            self.port.dtr = False
            self.port.setPort(self.device)
            self.port.open()
            self.connected = True
            return None
        except Exception as exc:  # noqa: BLE001 - report any open failure
            self.port = None
            self.connected = False
            return f"{type(exc).__name__}: {exc}"

    def close(self) -> None:
        with self._lock:
            if self.port is not None:
                try:
                    self.port.close()
                except Exception:  # noqa: BLE001
                    pass
            self.port = None
            self.connected = False

    def _buf_write(self, func: int, data: List[int]) -> None:
        if not self.connected or self.port is None:
            return
        buf = [0xAA, 0x55, int(func), len(data)]
        buf.extend(data)
        buf.append(_crc8(bytes(buf[2:])))
        with self._lock:
            try:
                self.port.write(bytes(buf))
            except Exception:  # noqa: BLE001
                self.connected = False

    def set_motor_type(self, motor_type: int = 0x02) -> None:
        # 0x05 sub-command, motor type byte
        self._buf_write(PACKET_FUNC_MOTOR, list(struct.pack("<BB", 0x05, motor_type)))

    def set_battery_level(self, battery_level: int = 0x1AF4) -> None:
        high = (battery_level >> 8) & 0xFF
        low = battery_level & 0xFF
        self._buf_write(PACKET_FUNC_SYS, list(struct.pack("BBB", 0x01, low, high)))

    def set_motor_speed(self, speeds: List[List[float]]) -> None:
        # Sub-command 0x01: count, then (motor_index_byte, rps_float) per motor.
        # Note: the firmware expects motor_index = id - 1.
        data = [0x01, len(speeds)]
        for motor_id, rps in speeds:
            data.extend(struct.pack("<Bf", int(motor_id) - 1, float(rps)))
        self._buf_write(PACKET_FUNC_MOTOR, data)


# ---------------------------------------------------------------------------
# Mecanum kinematics (lifted from driver/controller/controller/mecanum.py)
# ---------------------------------------------------------------------------


class _MecanumKinematics:
    """Convert (vx, vy, wz) to four wheel rps values.

    Layout (matches the legacy code)::

                x (forward)
            m1  ↑   m3
                |
            m2      m4

    The legacy implementation negated motors 1 and 2 before sending to
    the board to compensate for the physical wiring; we expose that
    pattern as the configurable ``directions`` list so other harnesses
    can override it without rewriting the math.
    """

    def __init__(
        self,
        wheelbase: float,
        track_width: float,
        wheel_diameter: float,
        directions: List[float],
        scales: List[float],
    ):
        self.wheelbase = wheelbase
        self.track_width = track_width
        self.wheel_diameter = wheel_diameter
        self.directions = directions
        self.scales = scales

    def _mps_to_rps(self, mps: float) -> float:
        # circumference = pi * d, so rps = mps / circumference
        return mps / (math.pi * self.wheel_diameter)

    def compute(self, vx: float, vy: float, wz: float) -> List[float]:
        half = (self.wheelbase + self.track_width) / 2.0
        m1 = vx - vy - wz * half
        m2 = vx + vy - wz * half
        m3 = vx + vy + wz * half
        m4 = vx - vy + wz * half
        wheel_mps = [m1, m2, m3, m4]
        rps = []
        for i, mps in enumerate(wheel_mps):
            signed = mps * self.directions[i] * self.scales[i]
            rps.append(self._mps_to_rps(signed))
        return rps


# ---------------------------------------------------------------------------
# ROS 2 node
# ---------------------------------------------------------------------------


class JazzyMecanumDriver(Node):
    def __init__(self) -> None:
        super().__init__("jazzy_mecanum_driver")

        # --- Geometry ---------------------------------------------------
        self.declare_parameter("wheelbase", 0.1368)
        self.declare_parameter("track_width", 0.1410)
        self.declare_parameter("wheel_diameter", 0.065)

        # --- Motor mapping ---------------------------------------------
        # IDs sent to the board for motors [front-left, rear-left,
        # front-right, rear-right]. Override if your wiring differs.
        self.declare_parameter("motor_ids", [1, 2, 3, 4])
        # Per-wheel sign. The legacy code applied [-1, -1, +1, +1]
        # because motors 1 and 2 are mounted mirrored on this chassis.
        self.declare_parameter("motor_directions", [-1.0, -1.0, 1.0, 1.0])
        # Per-wheel linear scale (unitless multiplier, defaults to 1.0).
        self.declare_parameter("motor_scales", [1.0, 1.0, 1.0, 1.0])

        # --- Limits / safety -------------------------------------------
        # Cap on |rps| sent to the board. 0 => no cap.
        self.declare_parameter("max_wheel_speed_rps", 8.0)
        # Drop to zero if no /cmd_vel arrives within this many seconds.
        self.declare_parameter("cmd_vel_timeout", 0.5)
        # Period at which we re-publish the latest command (and enforce
        # the timeout). 50 Hz matches the legacy controller cadence.
        self.declare_parameter("publish_period", 0.02)

        # --- Hardware interface ----------------------------------------
        self.declare_parameter("serial_port", "/dev/rrc")
        self.declare_parameter("baudrate", 1000000)
        self.declare_parameter("serial_timeout", 1.0)
        # JGB27 = 0x02, default for Mecanum (see legacy SDK comments).
        self.declare_parameter("motor_type", 0x02)
        # Battery level code (0x1af4 == 6.9V, the legacy Mecanum value).
        self.declare_parameter("battery_level", 0x1AF4)
        # If true, never touch the serial port -- log only.
        self.declare_parameter("dry_run", False)

        # --- Topics -----------------------------------------------------
        self.declare_parameter("cmd_vel_topic", "/cmd_vel")

        # --- Resolve params --------------------------------------------
        wheelbase = float(self.get_parameter("wheelbase").value)
        track_width = float(self.get_parameter("track_width").value)
        wheel_diameter = float(self.get_parameter("wheel_diameter").value)

        self.motor_ids = [int(x) for x in self.get_parameter("motor_ids").value]
        directions = [float(x) for x in self.get_parameter("motor_directions").value]
        scales = [float(x) for x in self.get_parameter("motor_scales").value]
        if not (len(self.motor_ids) == len(directions) == len(scales) == 4):
            raise ValueError(
                "motor_ids / motor_directions / motor_scales must each have length 4"
            )

        self.max_wheel_speed_rps = float(self.get_parameter("max_wheel_speed_rps").value)
        self.cmd_vel_timeout = float(self.get_parameter("cmd_vel_timeout").value)
        publish_period = float(self.get_parameter("publish_period").value)

        serial_port = str(self.get_parameter("serial_port").value)
        baudrate = int(self.get_parameter("baudrate").value)
        serial_timeout = float(self.get_parameter("serial_timeout").value)
        motor_type = int(self.get_parameter("motor_type").value)
        battery_level = int(self.get_parameter("battery_level").value)
        dry_run_param = self.get_parameter("dry_run")
        self.dry_run = bool(dry_run_param.value) if dry_run_param.type_ != Parameter.Type.NOT_SET else False

        cmd_vel_topic = str(self.get_parameter("cmd_vel_topic").value)

        # --- Kinematics -------------------------------------------------
        self.kin = _MecanumKinematics(
            wheelbase=wheelbase,
            track_width=track_width,
            wheel_diameter=wheel_diameter,
            directions=directions,
            scales=scales,
        )

        # --- Hardware ---------------------------------------------------
        self.board = _BoardLink(serial_port, baudrate, serial_timeout)
        if self.dry_run:
            self.get_logger().warn(
                "dry_run=True -- no serial port will be opened, commands logged only."
            )
        else:
            err = self.board.open()
            if err is not None:
                self.get_logger().warn(
                    f"Could not open serial port {serial_port} ({err}); "
                    "falling back to dry-run mode."
                )
                self.dry_run = True
            else:
                self.get_logger().info(
                    f"Connected to controller on {serial_port} @ {baudrate} baud."
                )
                # Match the legacy bring-up sequence.
                self.board.set_motor_type(motor_type)
                self.board.set_battery_level(battery_level)
                self.board.set_motor_speed([[mid, 0.0] for mid in self.motor_ids])

        # --- State ------------------------------------------------------
        self._latest_cmd = (0.0, 0.0, 0.0)  # vx, vy, wz
        self._last_cmd_stamp = self.get_clock().now()
        self._stopped = True
        self._state_lock = threading.Lock()

        # --- ROS interfaces --------------------------------------------
        self.create_subscription(Twist, cmd_vel_topic, self._on_cmd_vel, 10)
        self.timer = self.create_timer(publish_period, self._on_timer)

        self.get_logger().info(
            f"jazzy_mecanum_driver ready: subscribing to {cmd_vel_topic}, "
            f"publish_period={publish_period:.3f}s, "
            f"timeout={self.cmd_vel_timeout:.3f}s, dry_run={self.dry_run}."
        )

    # -- callbacks ------------------------------------------------------

    def _on_cmd_vel(self, msg: Twist) -> None:
        with self._state_lock:
            self._latest_cmd = (
                float(msg.linear.x),
                float(msg.linear.y),
                float(msg.angular.z),
            )
            self._last_cmd_stamp = self.get_clock().now()
            self._stopped = False

    def _on_timer(self) -> None:
        with self._state_lock:
            vx, vy, wz = self._latest_cmd
            last = self._last_cmd_stamp
            stopped = self._stopped

        now = self.get_clock().now()
        age = (now - last).nanoseconds * 1e-9

        if not stopped and age > self.cmd_vel_timeout:
            self.get_logger().warn(
                f"/cmd_vel timeout ({age:.2f}s > {self.cmd_vel_timeout:.2f}s) -- stopping."
            )
            self._send_stop()
            with self._state_lock:
                self._latest_cmd = (0.0, 0.0, 0.0)
                self._stopped = True
            return

        if stopped:
            # Periodically reassert zero so a transient missed packet
            # cannot leave the wheels turning.
            self._send_stop()
            return

        rps = self.kin.compute(vx, vy, wz)
        if self.max_wheel_speed_rps > 0.0:
            rps = [
                max(-self.max_wheel_speed_rps, min(self.max_wheel_speed_rps, r))
                for r in rps
            ]

        speeds = [[mid, r] for mid, r in zip(self.motor_ids, rps)]
        self._send_speeds(speeds)

    # -- hardware helpers ----------------------------------------------

    def _send_speeds(self, speeds: List[List[float]]) -> None:
        if self.dry_run or not self.board.connected:
            self.get_logger().debug(
                "dry-run speeds: " + ", ".join(f"id{m}={r:+.3f}rps" for m, r in speeds)
            )
            return
        try:
            self.board.set_motor_speed(speeds)
        except Exception as exc:  # noqa: BLE001
            self.get_logger().error(f"set_motor_speed failed: {exc}")

    def _send_stop(self) -> None:
        speeds = [[mid, 0.0] for mid in self.motor_ids]
        if self.dry_run or not self.board.connected:
            return
        try:
            self.board.set_motor_speed(speeds)
        except Exception as exc:  # noqa: BLE001
            self.get_logger().error(f"stop set_motor_speed failed: {exc}")

    # -- shutdown -------------------------------------------------------

    def safe_shutdown(self) -> None:
        try:
            self._send_stop()
            # belt-and-braces: send twice in case the first frame is lost
            time.sleep(0.01)
            self._send_stop()
        finally:
            self.board.close()


# TODO(hardware): the legacy stack also supports the following that this
# node intentionally does NOT handle, to keep "make the robot move" in a
# single file. Add them only if your application needs them:
#   * IMU / battery / button / joystick publishing (see
#     ros_robot_controller_node.py pub_callback).
#   * PWM and bus-servo control.
#   * RGB LEDs, OLED, buzzer.
# If you re-introduce them, mirror the message-passing pattern from the
# legacy node rather than expanding _BoardLink here.

# TODO(calibration): if your specific chassis uses different motor wiring,
# verify motor_directions experimentally:
#   1. Run with dry_run:=true and publish a small +x Twist.
#   2. Check that all four printed rps values have the sign you expect
#      for "forward" given your motor mounting.
#   3. Flip entries in motor_directions until they do, then save the
#      values to your launch / params file.


def main(args: Optional[List[str]] = None) -> None:
    rclpy.init(args=args)
    node = JazzyMecanumDriver()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.safe_shutdown()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
