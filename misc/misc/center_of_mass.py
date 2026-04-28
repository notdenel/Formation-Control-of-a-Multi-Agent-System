#!/usr/bin/env python3
# encoding: utf-8
"""
center_of_mass.py — Shared Center-of-Mass (CoM) position publisher and movement trigger.

Responsibilities:
    1. Maintains a mutable (x, y) CoM position in the global map frame.
    2. Publishes that position at a fixed rate on /center_of_mass/position
       (geometry_msgs/Point) so any agent can subscribe without polling.
    3. Exposes services so the CoM can be updated at any time:
         ~/set_position   (SetPose2D)  — overwrite CoM with an explicit (x, y)
         ~/get_position   (Trigger)    — read current CoM as a human-readable string
    4. Exposes a "trigger movement" service:
         ~/trigger_move   (Trigger)    — publishes a std_msgs/Empty on
                                         /center_of_mass/trigger so every
                                         subscribed agent starts navigating to
                                         the current CoM.

Why a separate trigger topic instead of calling each agent's service directly?
    The CoM node has no knowledge of how many agents exist or what their
    namespaces are. A latched Empty topic is a clean broadcast: any agent that
    subscribes will receive the trigger even if it connects after the call.

Topics published:
    /center_of_mass/position   geometry_msgs/Point  (10 Hz, latched)
    /center_of_mass/trigger    std_msgs/Empty        (latched, one-shot per trigger call)

Services:
    ~/set_position   interfaces/srv/SetPose2D  — update (x, y); z field is ignored
    ~/get_position   std_srvs/Trigger          — return current position as message
    ~/trigger_move   std_srvs/Trigger          — broadcast move trigger to all agents
"""

import threading
from typing import Optional

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, DurabilityPolicy, ReliabilityPolicy, HistoryPolicy

from geometry_msgs.msg import Point
from std_msgs.msg import Empty
from std_srvs.srv import Trigger
from interfaces.srv import SetPose2D


# ── QoS for the latched position topic ────────────────────────────────────────
# TRANSIENT_LOCAL + RELIABLE: late-joining subscribers receive the last value
# immediately without having to wait for the next 10 Hz publish tick.
_LATCHED_QOS = QoSProfile(
    depth=1,
    reliability=ReliabilityPolicy.RELIABLE,
    durability=DurabilityPolicy.TRANSIENT_LOCAL,
    history=HistoryPolicy.KEEP_LAST,
)

# ── QoS for the trigger topic ─────────────────────────────────────────────────
# Latched so agents that spin up *after* a trigger_move call still receive it.
_TRIGGER_QOS = QoSProfile(
    depth=1,
    reliability=ReliabilityPolicy.RELIABLE,
    durability=DurabilityPolicy.TRANSIENT_LOCAL,
    history=HistoryPolicy.KEEP_LAST,
)

# Default CoM coordinates (map origin). Override via ROS parameters
# 'initial_x' and 'initial_y' in a launch file.
DEFAULT_X = 0.0
DEFAULT_Y = 0.0

# Publish rate for the position topic (Hz).
PUBLISH_HZ = 10.0


class CenterOfMassNode(Node):
    """
    Publishes and manages the shared center-of-mass target position.

    All state access is guarded by self._lock so concurrent service calls
    (e.g. set_position while a publish tick fires) are race-free.
    """

    def __init__(self):
        super().__init__(
            'center_of_mass',
            allow_undeclared_parameters=True,
            automatically_declare_parameters_from_overrides=True,
        )

        self._lock = threading.Lock()

        # ── Initial CoM coordinates (overridable via ROS parameters) ──────────
        self.declare_parameter('initial_x', DEFAULT_X)
        self.declare_parameter('initial_y', DEFAULT_Y)
        init_x = self.get_parameter('initial_x').get_parameter_value().double_value
        init_y = self.get_parameter('initial_y').get_parameter_value().double_value

        self._com_x: float = init_x
        self._com_y: float = init_y

        # Track whether the position has ever been explicitly set so we can
        # warn agents that they may be navigating to a default.
        self._position_set: bool = False

        # ── Publishers ────────────────────────────────────────────────────────
        self._pos_pub = self.create_publisher(
            Point, '/center_of_mass/position', _LATCHED_QOS)

        self._trigger_pub = self.create_publisher(
            Empty, '/center_of_mass/trigger', _TRIGGER_QOS)

        # ── Services ──────────────────────────────────────────────────────────
        self.create_service(SetPose2D, '~/set_position',  self._set_position_cb)
        self.create_service(Trigger,   '~/get_position',  self._get_position_cb)
        self.create_service(Trigger,   '~/trigger_move',  self._trigger_move_cb)

        # ── Periodic publisher ────────────────────────────────────────────────
        self.create_timer(1.0 / PUBLISH_HZ, self._publish_position)

        # Publish immediately so late-joining agents get the initial value
        # from the latched topic without waiting up to 100 ms.
        self._publish_position()

        self.get_logger().info(
            f'center_of_mass ready — initial CoM: '
            f'x={self._com_x:.4f} y={self._com_y:.4f}'
        )

    # ──────────────────────────────────────────────────────────────────────────
    # Internal helpers
    # ──────────────────────────────────────────────────────────────────────────

    def _publish_position(self) -> None:
        """Publishes the current CoM as a geometry_msgs/Point (z=0)."""
        with self._lock:
            x = self._com_x
            y = self._com_y

        msg = Point()
        msg.x = x
        msg.y = y
        msg.z = 0.0
        self._pos_pub.publish(msg)

    # ──────────────────────────────────────────────────────────────────────────
    # Service callbacks
    # ──────────────────────────────────────────────────────────────────────────

    def _set_position_cb(self, request, response):
        """
        Updates the CoM position.

        request.data.x  — new x coordinate (map frame, metres)
        request.data.y  — new y coordinate (map frame, metres)
        request.data.z  — ignored (reserved for future 3-D extension)
        """
        new_x = float(request.data.x)
        new_y = float(request.data.y)

        with self._lock:
            old_x = self._com_x
            old_y = self._com_y
            self._com_x = new_x
            self._com_y = new_y
            self._position_set = True

        # Publish immediately so subscribers see the update without waiting
        # for the next periodic tick.
        self._publish_position()

        response.success = True
        response.message = (
            f'CoM updated: ({old_x:.4f}, {old_y:.4f}) → '
            f'({new_x:.4f}, {new_y:.4f})'
        )
        self.get_logger().info(response.message)
        return response

    def _get_position_cb(self, request, response):
        """Returns the current CoM position as a human-readable string."""
        with self._lock:
            x            = self._com_x
            y            = self._com_y
            position_set = self._position_set

        response.success = True
        response.message = (
            f'CoM position: x={x:.4f} y={y:.4f}'
            + ('' if position_set else ' [DEFAULT — set_position not yet called]')
        )
        return response

    def _trigger_move_cb(self, request, response):
        """
        Broadcasts a move trigger to all subscribed agents.

        Agents listening on /center_of_mass/trigger will receive the Empty
        message and begin navigating to the current CoM position. Because the
        topic is latched (TRANSIENT_LOCAL), an agent that connects after this
        call is made will still receive the trigger immediately upon subscribing.

        If the CoM has never been explicitly set (still at the default), a
        warning is included in the response so the caller can decide whether
        to proceed.
        """
        with self._lock:
            x            = self._com_x
            y            = self._com_y
            position_set = self._position_set

        self._trigger_pub.publish(Empty())

        warning = ''
        if not position_set:
            warning = (
                ' WARNING: CoM has not been explicitly set — '
                'agents will move to the default position '
                f'({DEFAULT_X:.4f}, {DEFAULT_Y:.4f}).'
            )
            self.get_logger().warning(warning.strip())

        response.success = True
        response.message = (
            f'Move trigger broadcast — agents should navigate to '
            f'x={x:.4f} y={y:.4f}.{warning}'
        )
        self.get_logger().info(
            f'trigger_move broadcast: target=({x:.4f}, {y:.4f})')
        return response


# ==============================================================================
# SECTION: Node Entry Point
# ==============================================================================

def main(args=None):
    """Initializes ROS 2 and spins the CenterOfMassNode."""
    rclpy.init(args=args)
    node = CenterOfMassNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
