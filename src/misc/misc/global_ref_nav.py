#!/usr/bin/env python3
# encoding: utf-8
"""
global_ref_nav.py - Mecanum-wheel linear navigator with object detection
                    + Center-of-Mass (CoM) cooperative movement.
Axes:
    y = forward / back  (positive y → forward)
    x = right  / left   (positive x → right)
Localisation pipeline (most → least trusted):
    1. AMCL             (/amcl_pose + /particle_cloud)
    2. RF2O laser odom  (/odom_rf2o)
    3. IMU              (/imu_corrected)
Services:
    set_reference           _set_reference_cb
    set_origin              _set_origin_cb
    get_imu_velocity        _get_imu_velocity_cb
Publishers:
    /imu_velocity           TwistStamped, 20 Hz
    /position               PoseStamped,  20 Hz  (x, y, yaw encoded in quaternion)
    /objects                String,       10 Hz  (formatted obstacle list)
CoM integration:
    Subscribes to  /center_of_mass/position  (geometry_msgs/Point, latched)
    → stores the latest CoM target and drives a PERSISTENT follower thread
        that continuously re-reads the latest position each tick.  The follower
        starts automatically on the first valid CoM position message and runs
        until the node shuts down.  It never exits on goal-reach; it simply
        idles (publishes stop) while dist <= GOAL_TOL and re-engages the moment
        the CoM position moves.
    Subscribes to  /center_of_mass/trigger   (std_msgs/Empty, latched)
    → retained for compatibility but no longer required to start following;
        ignored if the follower is already running.
    /center_of_mass/cancel  (std_msgs/Empty)
    → publishes a stop and suspends the follower until a new position or
        trigger message is received.
IMU velocity estimator:
    _ImuVelocityEstimator integrates linear_acceleration from /imu_corrected
    (body frame) with online bias removal and velocity decay.  A complementary
    filter blends the IMU integral with rf2o odometry velocity when available.
    The result is published on /imu_velocity (TwistStamped) at 20 Hz and
    queryable via ~/get_imu_velocity (Trigger service).
Rotation correction (holonomic platform):
    On every move-loop tick the current fused yaw is compared to the yaw
    captured at move-start.  If the drift exceeds 5 degrees a proportional
    counter-rotation torque is applied to cmd_vel.angular.z to bring the
    robot back to its original heading.
    NOTE: Yaw integration from the gyro (used only when AMCL and RF2O are
    both stale) is subject to gyro bias drift.  The bias estimator covers
    linear acceleration only; angular rate bias correction relies on AMCL /
    RF2O being available periodically to re-anchor the heading.
"""

import math
import threading
import time as _time
from enum import Enum, auto
from typing import Optional, List, Tuple, Dict
from dataclasses import dataclass
import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.executors import MultiThreadedExecutor
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.qos import QoSProfile, DurabilityPolicy, ReliabilityPolicy, HistoryPolicy
from std_msgs.msg import Empty, Float32, String
from std_srvs.srv import Trigger
from geometry_msgs.msg import (
    Twist, TwistStamped, PoseStamped,
    PoseWithCovarianceStamped, PoseArray,
    Point,
)
from nav_msgs.msg import Odometry
from sensor_msgs.msg import Imu, LaserScan
from interfaces.srv import SetPose2D
import tf2_ros
# ==============================================================================
# SECTION: Configuration & Constants
# ==============================================================================
# ── Motion limits ─────────────────────────────────────────────────────────────
MAX_SPEED             = 0.25
GOAL_TOL              = 0.05
LOOP_HZ               = 20
MOVE_TIMEOUT_BASE_S   = 1000.0
MOVE_TIMEOUT_PER_M_S  = 2000.0
POSITION_PUB_HZ       = 20
OBJECTS_PUB_HZ        = 10
_LOOP_PERIOD_S = 1.0 / LOOP_HZ

def _loop_sleep() -> None:
    _time.sleep(_LOOP_PERIOD_S)

# ── Object detection ──────────────────────────────────────────────────────────
OBJ_LIDAR_THRESHOLD    = 1.50
OBJ_CLUSTER_DIST       = 0.15
OBJ_MIN_CLUSTER_POINTS = 3
# ── LiDAR body-exclusion zone ─────────────────────────────────────────────────
OBJ_MIN_RANGE = 0.12
# ── Artificial Potential Field (APF) ──────────────────────────────────────────
APF_AVOID_RADIUS  = 1.00
APF_GAIN_A        = 0.10
APF_GAIN_R        = 0.01
APF_MIN_OBS_DIST  = 0.08
# ── Holonomic yaw-correction ──────────────────────────────────────────────────
YAW_CORRECTION_THRESH_RAD = math.radians(5.0)
YAW_CORRECTION_GAIN       = 2.5
YAW_CORRECTION_MAX_RAD_S  = 0.8
# ── Cross-sensor AMCL trust ───────────────────────────────────────────────────
AMCL_COV_ACCEPT        = 1.50
PARTICLE_SPREAD_THRESH = 1.20
AMCL_MAX_AGE_S         = 1.0
PARTICLE_MAX_AGE_S     = 2.0
# ── AMCL rejection escalation ────────────────────────────────────────────────
AMCL_REJECT_WARN_COUNT  = 5
AMCL_REJECT_ERROR_COUNT = 20
# ── Sensor staleness ──────────────────────────────────────────────────────────
IMU_MAX_AGE_S  = 0.5
RF2O_MAX_AGE_S = 1.0
ODOM_MAX_AGE_S = 1.0
SCAN_MAX_AGE_S = 0.5
# ── Complementary filter ──────────────────────────────────────────────────────
IMU_ALPHA = 0.20
# ── Gyro-only yaw watchdog ───────────────────────────────────────────────────
YAW_GYRO_ONLY_WARN_S  = 3.0
YAW_GYRO_ONLY_ERROR_S = 10.0
# ── CoM integration ───────────────────────────────────────────────────────────
COM_QOS = QoSProfile(
    depth=1,
    reliability=ReliabilityPolicy.RELIABLE,
    durability=DurabilityPolicy.TRANSIENT_LOCAL,
    history=HistoryPolicy.KEEP_LAST,
)
# ── QoS ───────────────────────────────────────────────────────────────────────
AMCL_QOS = QoSProfile(
    depth=1,
    reliability=ReliabilityPolicy.RELIABLE,
    durability=DurabilityPolicy.TRANSIENT_LOCAL,
)
SENSOR_QOS = QoSProfile(
    depth=1,
    reliability=ReliabilityPolicy.BEST_EFFORT,
    history=HistoryPolicy.KEEP_LAST,
)
CMD_VEL_QOS = QoSProfile(
    depth=1,
    reliability=ReliabilityPolicy.RELIABLE,
    history=HistoryPolicy.KEEP_LAST,
    durability=DurabilityPolicy.VOLATILE,
)
BEST_EFFORT_QOS = QoSProfile(
    depth=5,
    reliability=ReliabilityPolicy.BEST_EFFORT,
    history=HistoryPolicy.KEEP_LAST,
)
# ==============================================================================
# SECTION: Math & State Utility Functions
# ==============================================================================
class PositionState(Enum):
    """Tracks the reliability of the robot's estimated position based on sensor age."""
    UNINITIALISED = auto()
    DEGRADED      = auto()
    OK            = auto()
    READY         = auto()
def qua2yaw(o) -> float:
    """Converts a quaternion orientation into a yaw (Z-axis) angle."""
    return math.atan2(
        2.0 * (o.w * o.z + o.x * o.y),
        1.0 - 2.0 * (o.z * o.z + o.y * o.y),
    )
def wrap_angle(a: float) -> float:
    """Normalizes an angle to [-pi, pi]."""
    return (a + math.pi) % (2.0 * math.pi) - math.pi

def particle_cloud_spread(poses) -> float:
    """Calculates AMCL particle standard deviation to gauge localisation confidence.

    Returns float('inf') when fewer than 2 particles are available so that
    the caller's > PARTICLE_SPREAD_THRESH check correctly treats an
    under-populated cloud as unreliable rather than perfectly localised.
    """
    n = len(poses)
    if n < 2:
        return float('inf')
    mean_x = sum(p.position.x for p in poses) / n
    mean_y = sum(p.position.y for p in poses) / n
    return math.sqrt(
        sum((p.position.x - mean_x) ** 2 + (p.position.y - mean_y) ** 2
            for p in poses) / n
    )
@dataclass
class Position:
    x:   float = 0.0
    y:   float = 0.0
    yaw: float = 0.0
    vx:  float = 0.0
    vy:  float = 0.0
    def dist(self, other: "Position") -> float:
        return math.hypot(other.x - self.x, other.y - self.y)
# ==============================================================================
# SECTION: IMU Velocity Estimator
# ==============================================================================
class _ImuVelocityEstimator:
    """
    Estimates body-frame (forward, lateral) velocity by integrating IMU
    linear acceleration, with online bias removal and velocity decay.
    """
    DECAY_RATE          = 0.5
    BIAS_WARMUP_SAMPLES = 200
    DT_MIN              = 0.001
    DT_MAX              = 0.200
    CONFIDENCE_DECAY    = 2.0
    SPEED_SANITY_CAP    = 2.0
    def __init__(self):
        self.vx: float = 0.0
        self.vy: float = 0.0
        self._bias_ax:     float = 0.0
        self._bias_ay:     float = 0.0
        self._bias_n:      int   = 0
        self._bias_frozen: bool  = False
        self._last_stamp:  float = 0.0
        self.last_update:  float = 0.0
        self.sample_count: int   = 0
        self._motion_before_warmup: bool = False

    def freeze_bias_early(self) -> None:
        """Fix 8: Called when the robot is commanded to move before warm-up
        completes.  Freezes whatever bias has been accumulated so that real
        motion accelerations are not incorporated into the estimate, preventing
        a persistent velocity offset for the lifetime of the node.
        """
        if not self._bias_frozen:
            self._bias_frozen = True
            self._motion_before_warmup = True

    def update(self, ax_raw: float, ay_raw: float, stamp_s: float) -> None:
        if self._last_stamp <= 0.0:
            self._last_stamp = stamp_s
            self.last_update  = stamp_s
            self._accumulate_bias(ax_raw, ay_raw)
            return
        dt = stamp_s - self._last_stamp
        dt = max(self.DT_MIN, min(self.DT_MAX, dt))
        self._last_stamp  = stamp_s
        self.last_update  = stamp_s
        self.sample_count += 1
        if not self._bias_frozen:
            self._accumulate_bias(ax_raw, ay_raw)
            if self._bias_n >= self.BIAS_WARMUP_SAMPLES:
                self._bias_frozen = True
        ax = ax_raw - self._bias_ax
        ay = ay_raw - self._bias_ay
        decay   = math.exp(-self.DECAY_RATE * dt)
        self.vx = self.vx * decay + ax * dt
        self.vy = self.vy * decay + ay * dt
        speed = math.hypot(self.vx, self.vy)
        if speed > self.SPEED_SANITY_CAP:
            scale   = self.SPEED_SANITY_CAP / speed
            self.vx *= scale
            self.vy *= scale
    def blend_with_rf2o(self, rf2o_vx: float, rf2o_vy: float,
                        alpha: float = IMU_ALPHA) -> None:
        self.vx = alpha * self.vx + (1.0 - alpha) * rf2o_vx
        self.vy = alpha * self.vy + (1.0 - alpha) * rf2o_vy
    def confidence(self, now_s: float) -> float:
        if self.last_update <= 0.0:
            return 0.0
        age_cf  = max(0.0, 1.0 - (now_s - self.last_update) / self.CONFIDENCE_DECAY)
        bias_cf = 1.0 if self._bias_frozen else self._bias_n / self.BIAS_WARMUP_SAMPLES
        return age_cf * bias_cf
    def _accumulate_bias(self, ax: float, ay: float) -> None:
        self._bias_n += 1
        n = self._bias_n
        self._bias_ax += (ax - self._bias_ax) / n
        self._bias_ay += (ay - self._bias_ay) / n
# ==============================================================================
# SECTION: Main Node Class
# ==============================================================================
class GlobalRefNav(Node):
    def __init__(self):
        """Initializes the ROS 2 node, state variables, publishers, and callbacks."""
        super().__init__(
            'global_ref_nav',
            allow_undeclared_parameters=True,
            automatically_declare_parameters_from_overrides=True,
        )
        self._lock = threading.Lock()
        self._move_lock  = threading.Lock()
        self._move_owner: Optional[str] = None   # 'service' | 'com' | None
        self._est_x:           Optional[float] = None
        self._est_y:           Optional[float] = None
        self._fused_yaw:       Optional[float] = None
        self._fused_yaw_stamp: float = 0.0
        self._ref_x:   Optional[float] = None
        self._ref_y:   Optional[float] = None
        self._ref_yaw: Optional[float] = None
        self._amcl_stamp:      float = 0.0
        self._particle_spread: float = 0.0
        self._particle_stamp:  float = 0.0
        self._rf2o_stamp:      float = 0.0
        self._rf2o_yaw:        Optional[float] = None
        self._rf2o_x:          Optional[float] = None
        self._rf2o_y:          Optional[float] = None
        self._origin_x:   float = 0.0
        self._origin_y:   float = 0.0
        self._origin_yaw: float = 0.0
        self._imu_stamp:       float = 0.0
        self._imu_stamp_ros:   float = 0.0
        self._speed_limit:     float = MAX_SPEED
        self._scan:       Optional[LaserScan] = None
        self._scan_stamp: float               = 0.0
        self.position: Position = Position()
        self.position_state: PositionState = PositionState.UNINITIALISED
        self._last_cmd_stamp: float = 0.0
        self._active_objects: List[Dict] = []
        self._objects_stamp:  float = 0.0
        # ── CoM follower state (protected by self._lock) ──────────────────────
        # _com_x/_com_y  : latest target position from /center_of_mass/position
        # _com_follow_active : True while the follower thread is alive
        # _com_cancelled     : set True by /center_of_mass/cancel;
        #                      cleared when a new position arrives
        self._com_x:             Optional[float] = None
        self._com_y:             Optional[float] = None
        self._com_follow_active: bool = False
        self._com_cancelled:     bool = False
        # Gyro-only yaw watchdog state (protected by self._lock)
        self._gyro_only_since: Optional[float] = None
        self._amcl_reject_count: int = 0
        self._amcl_anchor_map_x:   Optional[float] = None
        self._amcl_anchor_map_y:   Optional[float] = None
        self._amcl_anchor_map_yaw: Optional[float] = None
        self._amcl_anchor_odom_x:  Optional[float] = None
        self._amcl_anchor_odom_y:  Optional[float] = None
        self._imu_vel        = _ImuVelocityEstimator()
        self._tf_broadcaster = tf2_ros.TransformBroadcaster(self)
        cb = ReentrantCallbackGroup()
        self.declare_parameter('cmd_vel_topic', 'controller/cmd_vel')
        cmd_topic = self.get_parameter('cmd_vel_topic').get_parameter_value().string_value
        self._cmd_pub = self.create_publisher(Twist, cmd_topic, CMD_VEL_QOS)
        self._imu_vel_pub  = self.create_publisher(TwistStamped, 'imu_velocity', CMD_VEL_QOS)
        self._position_pub = self.create_publisher(PoseStamped,  'position',     CMD_VEL_QOS)
        self._objects_pub  = self.create_publisher(String,       'objects',      BEST_EFFORT_QOS)
        self.create_subscription(PoseWithCovarianceStamped, 'amcl_pose',
                                self._amcl_cb, AMCL_QOS, callback_group=cb)
        self.create_subscription(PoseArray, '/particle_cloud',
                                self._particle_cloud_cb, SENSOR_QOS, callback_group=cb)
        self.create_subscription(Odometry, 'odom_rf2o',
                                self._rf2o_cb, SENSOR_QOS, callback_group=cb)
        self.create_subscription(Imu, 'imu_corrected',
                                self._imu_cb, SENSOR_QOS, callback_group=cb)
        self.create_subscription(LaserScan, 'scan_raw',
                                self._scan_cb, SENSOR_QOS, callback_group=cb)
        self.create_subscription(Float32, '/speed_limit',
                                self._speed_limit_cb, BEST_EFFORT_QOS, callback_group=cb)
        self.create_subscription(
            Point, '/center_of_mass/position',
            self._com_position_cb, COM_QOS, callback_group=cb)
        self.create_subscription(
            Empty, '/center_of_mass/trigger',
            self._com_trigger_cb, COM_QOS, callback_group=cb)
        self.create_subscription(
            Empty, '/center_of_mass/cancel',
            self._com_cancel_cb, COM_QOS, callback_group=cb)
        self.create_service(Trigger,   '~/set_reference',         self._set_reference_cb)
        self.create_service(Trigger,   '~/set_origin',            self._set_origin_cb)
        self.create_service(Trigger,   '~/stop_move',            self._stop_move_cb)
        self.create_service(SetPose2D, '~/move_to_relative_goal', self._move_cb,
                            callback_group=cb)
        self.create_service(Trigger, '~/get_imu_velocity',
                            self._get_imu_velocity_cb, callback_group=cb)
        self.create_timer(0.1,                   self._update_objects_timer, callback_group=cb)
        self.create_timer(1.0 / LOOP_HZ,         self._publish_imu_velocity, callback_group=cb)
        self.create_timer(1.0 / POSITION_PUB_HZ, self._publish_position,     callback_group=cb)
        self.create_timer(1.0 / OBJECTS_PUB_HZ,  self._publish_objects,      callback_group=cb)
        self.get_logger().info('global_ref_nav ready')
    # ==============================================================================
    # SECTION: Core Helper Methods
    # ==============================================================================
    def _get_now_s(self) -> float:
        return self.get_clock().now().nanoseconds * 1e-9
    def _check_yaw_freshness(self, now: float) -> None:
        """
        Gyro-only yaw watchdog.
        MUST be called while self._lock is held.
        When both AMCL and RF2O are stale the fused yaw is driven purely by
        IMU gyro integration which accumulates bias with no correction.
        Tracks how long that condition persists and:
        - warns  after YAW_GYRO_ONLY_WARN_S  seconds
        - errors + forces DEGRADED after YAW_GYRO_ONLY_ERROR_S seconds
        so that move loops abort rather than navigate with drifted heading.

        Fix 6: The watchdog is only applied as a downgrade; the upgrade path
        in _update_public_position separately checks amcl_fresh / rf2o_fresh
        AFTER this call so that a sensor coming back online on the same tick
        is correctly recognised and the state is upgraded without waiting an
        extra cycle.
        """
        amcl_age = now - self._amcl_stamp
        rf2o_age = now - self._rf2o_stamp
        if amcl_age < AMCL_MAX_AGE_S or rf2o_age < RF2O_MAX_AGE_S:
            self._gyro_only_since = None   # anchored — reset watchdog
            return
        if self._fused_yaw is None:
            return
        if self._gyro_only_since is None:
            self._gyro_only_since = now
        drift_s = now - self._gyro_only_since
        if drift_s >= YAW_GYRO_ONLY_ERROR_S:
            self.position_state = PositionState.DEGRADED
            self.get_logger().error(
                f'Yaw has been gyro-only for {drift_s:.1f}s - position DEGRADED. '
                f'AMCL age={amcl_age:.1f}s RF2O age={rf2o_age:.1f}s.',
                throttle_duration_sec=5.0)
        elif drift_s >= YAW_GYRO_ONLY_WARN_S:
            self.get_logger().warning(
                f'Yaw is gyro-only for {drift_s:.1f}s (no AMCL/RF2O anchor). '
                f'Heading may be drifting.',
                throttle_duration_sec=2.0)
    def _update_public_position(self) -> None:
        """MUST be called while self._lock is held."""
        if self._est_x is None or self._est_y is None or self._fused_yaw is None:
            self.position_state = PositionState.UNINITIALISED
            return
        cos_o = math.cos(-self._origin_yaw)
        sin_o = math.sin(-self._origin_yaw)
        dx    = self._est_x - self._origin_x
        dy    = self._est_y - self._origin_y
        self.position = Position(
            x   =  cos_o * dx - sin_o * dy,
            y   =  sin_o * dx + cos_o * dy,
            yaw = wrap_angle(self._fused_yaw - self._origin_yaw),
            vx  = self._imu_vel.vx,
            vy  = self._imu_vel.vy,
        )
        now = self._get_now_s()
        amcl_fresh = 0.0 < self._amcl_stamp and (now - self._amcl_stamp) < AMCL_MAX_AGE_S
        rf2o_fresh = 0.0 < self._rf2o_stamp and (now - self._rf2o_stamp) < RF2O_MAX_AGE_S
        imu_fresh  = 0.0 < self._imu_stamp  and (now - self._imu_stamp)  < IMU_MAX_AGE_S
        ref_set    = self._ref_x is not None

        self._check_yaw_freshness(now)

        if amcl_fresh or rf2o_fresh:
            # Fresh anchor available — unconditionally re-evaluate upward.
            if amcl_fresh and ref_set:
                self.position_state = PositionState.READY
            else:
                self.position_state = PositionState.OK
        elif self.position_state != PositionState.DEGRADED:
            # No anchor, not already degraded by watchdog — apply normal logic.
            if imu_fresh:
                self.position_state = PositionState.OK
            else:
                self.position_state = PositionState.DEGRADED
        # If state is DEGRADED and no fresh anchor arrived, leave it as-is
        # (watchdog may have just set it, or it was already set).

    def _update_objects_timer(self) -> None:
        with self._lock:
            state      = self.position_state
            scan       = self._scan
            scan_stamp = self._scan_stamp
            robot_x    = self.position.x
            robot_y    = self.position.y
            robot_yaw  = self.position.yaw
        if state == PositionState.UNINITIALISED or scan is None:
            return
        if (self._get_now_s() - scan_stamp) > SCAN_MAX_AGE_S:
            with self._lock:
                self._active_objects = []
            return
        objects = self._detect_objects(scan, robot_x, robot_y, robot_yaw, OBJ_LIDAR_THRESHOLD)
        with self._lock:
            self._active_objects = objects
            self._objects_stamp  = self._get_now_s()
    def _publish_cmd(self, vx: float, vy: float, wz: float = 0.0) -> None:
        """
        Publishes a Twist velocity command.
            linear.x  = forward / back   (positive → forward, +vx)
            linear.y  = right  / left    (positive → right,   +vy)
            angular.z = yaw rate         (positive → CCW)
        Threading: may be called concurrently from service and CoM-follower
        threads; _last_cmd_stamp is written under self._lock (Fix 12).
        """
        cmd = Twist()
        cmd.linear.x  = float(vx)   # forward (+vy moves forward)
        cmd.linear.y  = float(vy)   # lateral (+vy moves right)
        cmd.linear.z  = 0.0
        cmd.angular.x = 0.0
        cmd.angular.y = 0.0
        cmd.angular.z = float(wz)
        self._cmd_pub.publish(cmd)
        with self._lock:
            self._last_cmd_stamp = self._get_now_s()
        
    def _publish_stop(self) -> None:
        self._publish_cmd(0.0, 0.0, 0.0)
    # ==============================================================================
    # SECTION: Sensor Callbacks
    # ==============================================================================
    def _amcl_cb(self, msg: PoseWithCovarianceStamped) -> None:
        cov     = msg.pose.covariance
        pos_cov = max(cov[0], cov[7])
        with self._lock:
            if pos_cov > AMCL_COV_ACCEPT:
                self._amcl_reject_count += 1
                n = self._amcl_reject_count
                # Log outside the lock so we don't hold it during I/O.
                do_error = n >= AMCL_REJECT_ERROR_COUNT
                do_warn  = n >= AMCL_REJECT_WARN_COUNT
            else:
                self._amcl_reject_count = 0
                n = 0
                do_error = False
                do_warn  = False

        self.get_logger().info(
            f'AMCL raw cov[0]={cov[0]:.4f} cov[7]={cov[7]:.4f} '
            f'spread={self._particle_spread:.3f}',
            throttle_duration_sec=1.0)
        if pos_cov > AMCL_COV_ACCEPT:
            if do_error:
                self.get_logger().error(
                    f'AMCL rejected {n} consecutive poses '
                    f'(cov={pos_cov:.4f} > {AMCL_COV_ACCEPT}). '
                    f'Localisation may be lost.',
                    throttle_duration_sec=5.0)
            elif do_warn:
                self.get_logger().warning(
                    f'AMCL rejected {n} consecutive poses '
                    f'(cov={pos_cov:.4f} > {AMCL_COV_ACCEPT}).',
                    throttle_duration_sec=2.0)
            else:
                self.get_logger().warning(
                    f'AMCL cov {pos_cov:.4f} > {AMCL_COV_ACCEPT} - rejected.',
                    throttle_duration_sec=2.0)
            return

        amcl_x   = msg.pose.pose.position.x
        amcl_y   = msg.pose.pose.position.y
        amcl_yaw = qua2yaw(msg.pose.pose.orientation)
        now      = self._get_now_s()
        with self._lock:
            if (now - self._particle_stamp) < PARTICLE_MAX_AGE_S and \
                    self._particle_spread > PARTICLE_SPREAD_THRESH:
                self.get_logger().warning(
                    f'AMCL spread ={self._particle_spread:.3f}m',
                    throttle_duration_sec=2.0)
                return
            self._est_x           = amcl_x
            self._est_y           = amcl_y
            self._fused_yaw       = amcl_yaw
            self._fused_yaw_stamp = now
            self._amcl_stamp      = now
            self._amcl_anchor_map_x   = amcl_x
            self._amcl_anchor_map_y   = amcl_y
            self._amcl_anchor_map_yaw = amcl_yaw
            self._amcl_anchor_odom_x  = self._rf2o_x
            self._amcl_anchor_odom_y  = self._rf2o_y
            self._update_public_position()
    def _particle_cloud_cb(self, msg: PoseArray) -> None:
        spread = particle_cloud_spread(msg.poses)
        with self._lock:
            self._particle_spread = spread
            self._particle_stamp  = self._get_now_s()
    def _rf2o_cb(self, msg: Odometry) -> None:
        new_x   = msg.pose.pose.position.x
        new_y   = msg.pose.pose.position.y
        new_yaw = qua2yaw(msg.pose.pose.orientation)
        now     = self._get_now_s()
        rf2o_vx = float(msg.twist.twist.linear.x)   # forward velocity
        rf2o_vy = float(msg.twist.twist.linear.y)   # lateral velocity
        with self._lock:
            amcl_fresh = (now - self._amcl_stamp) < AMCL_MAX_AGE_S
            if not amcl_fresh:
                if self._amcl_anchor_map_x is not None and \
                        self._amcl_anchor_odom_x is not None:
                    anchor_map_x   = self._amcl_anchor_map_x
                    anchor_map_y   = self._amcl_anchor_map_y
                    anchor_map_yaw = self._amcl_anchor_map_yaw
                    anchor_odom_x  = self._amcl_anchor_odom_x
                    anchor_odom_y  = self._amcl_anchor_odom_y
                    d_odom_x = new_x - anchor_odom_x
                    d_odom_y = new_y - anchor_odom_y
                    cos_a    = math.cos(anchor_map_yaw)
                    sin_a    = math.sin(anchor_map_yaw)
                    self._est_x = (anchor_map_x
                                + cos_a * d_odom_x - sin_a * d_odom_y)
                    self._est_y = (anchor_map_y
                                + sin_a * d_odom_x + cos_a * d_odom_y)
                elif self._est_x is not None and self._rf2o_x is not None:
                    self._est_x += new_x - self._rf2o_x
                    self._est_y += new_y - self._rf2o_y
                elif self._est_x is None:
                    self._est_x = new_x
                    self._est_y = new_y
                if self._fused_yaw is None:
                    self._fused_yaw = new_yaw
                elif self._rf2o_yaw is not None:
                    delta = wrap_angle(new_yaw - self._rf2o_yaw)
                    self._fused_yaw = wrap_angle(self._fused_yaw + delta)
                self._fused_yaw_stamp = now
            self._rf2o_x     = new_x
            self._rf2o_y     = new_y
            self._rf2o_yaw   = new_yaw
            self._rf2o_stamp = now
            self._imu_vel.blend_with_rf2o(rf2o_vx, rf2o_vy, alpha=IMU_ALPHA)
            self._update_public_position()
    def _imu_cb(self, msg: Imu) -> None:
        """
        IMU callback.
        Angular velocity (gyro) is integrated for yaw only when both AMCL and
        RF2O are stale.  This path is a short-term fallback; the watchdog in
        _check_yaw_freshness degrades state after YAW_GYRO_ONLY_ERROR_S.
        """
        now_ros  = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9
        now_mono = self._get_now_s()
        ax_raw = float(msg.linear_acceleration.x)   # forward axis (+vx forward)
        ay_raw = float(msg.linear_acceleration.y)   # lateral axis (+vy right)
        with self._lock:
            amcl_fresh = (now_mono - self._amcl_stamp) < AMCL_MAX_AGE_S
            rf2o_fresh = (now_mono - self._rf2o_stamp) < RF2O_MAX_AGE_S
            if not amcl_fresh and not rf2o_fresh:
                if self._imu_stamp_ros > 0.0 and self._fused_yaw is not None:
                    dt = now_ros - self._imu_stamp_ros
                    if 0.0 < dt < 0.5:
                        self._fused_yaw = wrap_angle(
                            self._fused_yaw + msg.angular_velocity.z * dt)
                        self._fused_yaw_stamp = now_mono
            self._imu_stamp_ros = now_ros
            self._imu_stamp     = now_mono
            self._update_public_position()
            self._imu_vel.update(ax_raw, ay_raw, now_ros)
    def _scan_cb(self, msg: LaserScan) -> None:
        with self._lock:
            self._scan       = msg
            self._scan_stamp = self._get_now_s()
    def _speed_limit_cb(self, msg: Float32) -> None:
        with self._lock:
            if msg.data < 0.0:
                self._speed_limit = MAX_SPEED
            else:
                self._speed_limit = min(MAX_SPEED, float(msg.data))
    # ==============================================================================
    # SECTION: IMU Velocity Publisher & Service
    # ==============================================================================
    def _build_imu_velocity_msg(self) -> TwistStamped:
        """MUST be called while self._lock is held."""
        msg = TwistStamped()
        msg.header.stamp    = self.get_clock().now().to_msg()
        msg.header.frame_id = 'map'
        vx_body = self._imu_vel.vx
        vy_body = self._imu_vel.vy
        yaw     = self._fused_yaw if self._fused_yaw is not None else 0.0
        cos_h   = math.cos(yaw)
        sin_h   = math.sin(yaw)
        vx_world =  cos_h * vx_body - sin_h * vy_body
        vy_world =  sin_h * vx_body + cos_h * vy_body
        speed    = math.hypot(vx_world, vy_world)
        conf     = self._imu_vel.confidence(self._get_now_s())
        msg.twist.linear.x  = vx_world
        msg.twist.linear.y  = vy_world
        msg.twist.linear.z  = speed
        msg.twist.angular.x = vx_body
        msg.twist.angular.y = vy_body
        msg.twist.angular.z = conf
        return msg
    def _publish_imu_velocity(self) -> None:
        with self._lock:
            if self._imu_vel.last_update <= 0.0:
                return
            msg = self._build_imu_velocity_msg()
        self._imu_vel_pub.publish(msg)
    def _get_imu_velocity_cb(self, request, response):
        with self._lock:
            last_update = self._imu_vel.last_update
            conf        = self._imu_vel.confidence(self._get_now_s())
            sample_n    = self._imu_vel.sample_count
            bias_frozen = self._imu_vel._bias_frozen
            vx_body     = self._imu_vel.vx
            vy_body     = self._imu_vel.vy
            yaw         = self._fused_yaw if self._fused_yaw is not None else 0.0
            pos_state   = self.position_state
        now = self._get_now_s()
        if last_update <= 0.0:
            response.success = False
            response.message = 'IMU velocity estimator has not received any data yet.'
            return response
        age = now - last_update
        if age > IMU_MAX_AGE_S:
            response.success = False
            response.message = (
                f'IMU velocity data is stale '
                f'(age={age:.2f}s > limit={IMU_MAX_AGE_S}s).')
            return response
        if conf < 0.10:
            response.success = False
            response.message = (
                f'IMU velocity confidence too low ({conf:.2f}) - '
                f'bias warmup in progress '
                f'({sample_n}/{_ImuVelocityEstimator.BIAS_WARMUP_SAMPLES} samples).')
            return response
        cos_h    =  math.cos(yaw)
        sin_h    =  math.sin(yaw)
        vx_world =  cos_h * vx_body - sin_h * vy_body
        vy_world =  sin_h * vx_body + cos_h * vy_body
        speed    = math.hypot(vx_world, vy_world)
        heading  = math.degrees(math.atan2(vy_world, vx_world))
        flags = []
        if not bias_frozen:
            flags.append('BIAS_WARMUP')
        if pos_state == PositionState.DEGRADED:
            flags.append('POS_DEGRADED')
        if age > IMU_MAX_AGE_S * 0.5:
            flags.append('AGING')
        flag_str = (' [' + ' '.join(flags) + ']') if flags else ''
        response.success = True
        response.message = (
            f'body: fwd={vx_body:+.4f}m/s lat={vy_body:+.4f}m/s  '
            f'world: vx={vx_world:+.4f}m/s vy={vy_world:+.4f}m/s  '
            f'speed={speed:.4f}m/s head={heading:+.1f}deg  '
            f'conf={conf:.2f} age={age:.3f}s samples={sample_n}'
            + flag_str
        )
        return response
    # ==============================================================================
    # SECTION: Center-of-Mass Callbacks
    # ==============================================================================
    def _com_position_cb(self, msg: Point) -> None:
        """
        Stores the latest CoM position and starts the persistent follower thread
        if it is not already running.
        A new position message also clears any prior cancel so the follower
        resumes immediately without needing a trigger.
        """
        with self._lock:
            self._com_x        = float(msg.x)
            self._com_y        = float(msg.y)
            self._com_cancelled = False   # new position clears any cancel
            already_running    = self._com_follow_active
            state              = self.position_state
        self.get_logger().debug(
            f'CoM position updated: x={msg.x:.4f} y={msg.y:.4f}',
            throttle_duration_sec=2.0)
        if not already_running and state != PositionState.UNINITIALISED:
            self._start_com_follower()
    def _com_trigger_cb(self, msg: Empty) -> None:
        """
        Legacy trigger — retained for compatibility.
        Starts the follower if not already running.
        """
        with self._lock:
            com_x          = self._com_x
            com_y          = self._com_y
            already_running = self._com_follow_active
        if com_x is None or com_y is None:
            self.get_logger().error(
                'CoM trigger received but no CoM position has been published yet - '
                'ignoring. Make sure center_of_mass.py is running.')
            return
        if already_running:
            self.get_logger().info(
                'CoM trigger received - follower already running, ignoring.')
            return
        self.get_logger().info(
            f'CoM trigger received - starting follower '
            f'(initial target x={com_x:.4f} y={com_y:.4f})')
        self._start_com_follower()
    def _com_cancel_cb(self, msg: Empty) -> None:
        """
        Suspends CoM following.  Sets _com_cancelled so the follower thread
        idles (stop commands) until a new /center_of_mass/position arrives.
        """
        with self._lock:
            self._com_cancelled = True
        self._publish_stop()
        self.get_logger().info('[CoM follower] Cancelled via /center_of_mass/cancel.')
    def _start_com_follower(self) -> None:
        """
        Spawns the persistent CoM follower thread.
        Safe to call from any context; no-ops if thread is already running.
        Must be called OUTSIDE self._lock.
        """
        with self._lock:
            if self._com_follow_active:
                return
            self._com_follow_active = True
        t = threading.Thread(
            target=self._run_com_follower,
            daemon=True,
            name='com_follower',
        )
        t.start()
        self.get_logger().info('[CoM follower] Thread started.')
    def _run_com_follower(self) -> None:
        self.get_logger().info('[CoM follower] Running — will track CoM continuously.')
        try:
            while rclpy.ok():
                try:
                    with self._lock:
                        com_x      = self._com_x
                        com_y      = self._com_y
                        cancelled  = self._com_cancelled
                        cur_x      = self.position.x
                        cur_y      = self.position.y
                        state      = self.position_state
                    # ── Idle conditions ────────────────────────────────────────
                    if cancelled or com_x is None or com_y is None:
                        self._publish_stop()
                        _loop_sleep()
                        continue
                    if state == PositionState.UNINITIALISED:
                        self.get_logger().warning(
                            '[CoM follower] Position uninitialised — waiting.',
                            throttle_duration_sec=5.0)
                        _loop_sleep()
                        continue
                    dist = math.hypot(com_x - cur_x, com_y - cur_y)
                    if dist <= GOAL_TOL:
                        # At goal — idle; re-engage when target moves
                        self._publish_stop()
                        _loop_sleep()
                        continue
                    # ── Drive toward current CoM target ────────────────────────
                    self.get_logger().debug(
                        f'[CoM follower] Moving to x={com_x:.4f} y={com_y:.4f} '
                        f'dist={dist:.3f}m',
                        throttle_duration_sec=1.0)
                    # live_goal=True: _run_move_loop re-reads _com_x/_com_y each
                    # inner tick so the robot steers toward the moving target
                    # without restarting the loop.
                    self._run_move_loop(
                        goal_x=com_x,
                        goal_y=com_y,
                        log_prefix='[CoM follower]',
                        owner='com',
                        live_goal=True,
                    )
                    # Immediately loop back — re-evaluate whether target has moved.
                except Exception as exc: 
                    self.get_logger().error(
                        f'[CoM follower] Unhandled exception in loop body: {exc}',
                        throttle_duration_sec=2.0)
                    _loop_sleep()
        finally:
            self._publish_stop()
            with self._lock:
                self._com_follow_active = False
            self.get_logger().info('[CoM follower] Thread exiting.')
    # ==============================================================================
    # SECTION: Move Loop + Helper Functions
    # ==============================================================================
    def _run_move_loop(
        self,
        goal_x:     float,
        goal_y:     float,
        log_prefix: str  = '[move]',
        owner:      str  = 'unknown',
        live_goal:  bool = False,
    ) -> bool:
        """
        Parameters
        ----------
        goal_x, goal_y : float
            Initial target in origin-relative frame.
        log_prefix : str
            Prepended to log messages.
        owner : str
            Stored in _move_owner while the lock is held.
        live_goal : bool
            When True, _run_move_loop_inner re-reads _com_x/_com_y every tick
            so the robot follows a moving target.
        """
        if not self._move_lock.acquire(blocking=False):
            with self._lock:
                current_owner = self._move_owner
            self.get_logger().warning(
                f'{log_prefix} Move rejected — lock held by owner={current_owner}.')
            return False
        with self._lock:
            self._move_owner = owner
            if not self._imu_vel._bias_frozen:
                self.get_logger().warning(
                    f'{log_prefix} IMU bias warm-up incomplete — freezing bias '
                    f'early to avoid motion contamination '
                    f'({self._imu_vel._bias_n}/'
                    f'{_ImuVelocityEstimator.BIAS_WARMUP_SAMPLES} samples).')
                self._imu_vel.freeze_bias_early()
        try:
            return self._run_move_loop_inner(
                goal_x=goal_x,
                goal_y=goal_y,
                log_prefix=log_prefix,
                live_goal=live_goal,
            )
        finally:
            with self._lock:
                self._move_owner = None
            self._move_lock.release()
    def _run_move_loop_inner(
        self,
        goal_x:     float,
        goal_y:     float,
        log_prefix: str,
        live_goal:  bool,
    ) -> bool:
        with self._lock:
            state     = self.position_state
            cur_x     = self.position.x
            cur_y     = self.position.y
            fused_yaw = self._fused_yaw
        if state == PositionState.UNINITIALISED:
            self.get_logger().error(
                f'{log_prefix} Cannot move: position not initialised.')
            return False
        if fused_yaw is None:
            self.get_logger().error(
                f'{log_prefix} Cannot move: fused yaw not yet available.')
            return False
        start_yaw = fused_yaw

        move_dist    = math.hypot(goal_x - cur_x, goal_y - cur_y)
        move_timeout = MOVE_TIMEOUT_BASE_S + move_dist * MOVE_TIMEOUT_PER_M_S
        move_start   = self._get_now_s()
        success = False
        while rclpy.ok():
            now     = self._get_now_s()
            elapsed = now - move_start

            with self._lock:
                cur_x          = self.position.x
                cur_y          = self.position.y
                raw_yaw        = self._fused_yaw if self._fused_yaw is not None else start_yaw
                eff_max_spd    = self._speed_limit
                state          = self.position_state
                active_objects = list(self._active_objects)
                objects_fresh  = (self._get_now_s() - self._objects_stamp) < SCAN_MAX_AGE_S
                # Live goal: re-read CoM target each tick (continuous following)
                if live_goal:
                    if self._com_cancelled or self._com_x is None:
                        self.get_logger().info(
                            f'{log_prefix} CoM cancelled or position cleared — exiting loop.')
                        break
                    goal_x = self._com_x
                    goal_y = self._com_y

            if live_goal:
                live_dist    = math.hypot(goal_x - cur_x, goal_y - cur_y)
                move_timeout = MOVE_TIMEOUT_BASE_S + live_dist * MOVE_TIMEOUT_PER_M_S
                # elapsed is measured from move_start; reset start to keep the
                # window rolling rather than accumulating indefinitely.
                if elapsed > move_timeout:
                    move_start = now
                    elapsed    = 0.0
            else:
                if elapsed > move_timeout:
                    self.get_logger().error(
                        f'{log_prefix} Timeout after {elapsed:.1f}s '
                        f'(budget={move_timeout:.1f}s, dist={move_dist:.2f}m) - aborting.')
                    break

            if state == PositionState.UNINITIALISED:
                self.get_logger().error(
                    f'{log_prefix} Position lost mid-move - aborting.')
                break
            err_x = goal_x - cur_x
            err_y = goal_y - cur_y
            dist  = math.hypot(err_x, err_y)
            if dist <= GOAL_TOL:
                success = True
                break
            # ── Attraction force (origin-relative frame) ───────────────────────
            f_ax = APF_GAIN_A * err_x
            f_ay = APF_GAIN_A * err_y
            # ── Repulsive force ────────────────────────────────────────────────
            f_rx = 0.0
            f_ry = 0.0
            # if objects_fresh and active_objects:
            #     for obj in active_objects:
            #         # world → origin-relative
            #         dox = obj['world_x'] - self._origin_x
            #         doy = obj['world_y'] - self._origin_y
            #         obs_x =  math.cos(-self._origin_yaw) * dox - math.sin(-self._origin_yaw) * doy
            #         obs_y =  math.sin(-self._origin_yaw) * dox + math.cos(-self._origin_yaw) * doy
            #         obs_dist = max(obj['distance'], APF_MIN_OBS_DIST)
            #         if obs_dist < APF_AVOID_RADIUS:
            #             rep_mag  = APF_GAIN_R * (1.0 / obs_dist - 1.0 / APF_AVOID_RADIUS)
            #             obs_dx   = cur_x - obs_x
            #             obs_dy   = cur_y - obs_y
            #             obs_norm = math.hypot(obs_dx, obs_dy)
            #             if obs_norm > 1e-6:
            #                 f_rx += rep_mag * (obs_dx / obs_norm)
            #                 f_ry += rep_mag * (obs_dy / obs_norm)
            # ── Combined velocity (origin-relative frame) ──────────────────────
            cmd_world_x = f_ax - f_rx
            cmd_world_y = f_ay - f_ry
            cmd_speed = math.hypot(cmd_world_x, cmd_world_y)
            if cmd_speed > eff_max_spd:
                scale        = eff_max_spd
                cmd_world_x *= scale
                cmd_world_y *= scale
            # ── World → body-frame ─────────────────────────────────────────────
            cos_h = math.cos(raw_yaw)
            sin_h = math.sin(raw_yaw)
            # +vx = forward, +vy = right (mecanum convention per node docstring)
            v_fwd =  cos_h * cmd_world_x + sin_h * cmd_world_y
            v_lat = -sin_h * cmd_world_x + cos_h * cmd_world_y
            # ── Yaw-drift correction ───────────────────────────────────────────
            yaw_error = wrap_angle(raw_yaw - start_yaw)
            wz = 0.0
            if dist > GOAL_TOL and abs(yaw_error) > YAW_CORRECTION_THRESH_RAD:
                wz = max(
                    -YAW_CORRECTION_MAX_RAD_S,
                    min(YAW_CORRECTION_MAX_RAD_S, -YAW_CORRECTION_GAIN * yaw_error),
                )
                self.get_logger().debug(
                    f'{log_prefix} Yaw correction: '
                    f'err={math.degrees(yaw_error):.1f}° wz={wz:.3f}rad/s',
                    throttle_duration_sec=1.0)
            self._publish_cmd(0, v_fwd, wz)
            _loop_sleep()
        return success
    # ==============================================================================
    # SECTION: Spatial Algorithms (Clustering)
    # ==============================================================================
    def _scan_to_points(self, scan: LaserScan, robot_x: float, robot_y: float,
                        robot_yaw: float, radius: float) -> List[Tuple[float, float]]:
        """
        Converts a LaserScan into world-frame (x, y) points within `radius`.
        Returns shorter than OBJ_MIN_RANGE are discarded to eliminate chassis self-returns.
        """
        points = []
        for i, r in enumerate(scan.ranges):
            if not math.isfinite(r) or r < OBJ_MIN_RANGE or r > min(scan.range_max, radius):
                continue
            bearing     = scan.angle_min + i * scan.angle_increment
            world_angle = bearing + robot_yaw
            wx = robot_x + r * math.cos(world_angle)
            wy = robot_y + r * math.sin(world_angle)
            points.append((wx, wy))
        return points
    def _cluster_points(self, points: List[Tuple[float, float]]) -> List[List[Tuple[float, float]]]:
        """
        Groups nearby LiDAR points into discrete obstacle clusters using a
        grid-bucketed BFS.  O(n) average complexity.
        """
        if not points:
            return []
        cell = OBJ_CLUSTER_DIST
        grid: Dict[Tuple[int, int], List[int]] = {}
        for idx, (px, py) in enumerate(points):
            key = (int(math.floor(px / cell)), int(math.floor(py / cell)))
            grid.setdefault(key, []).append(idx)
        assigned = [False] * len(points)
        clusters = []
        for start_idx in range(len(points)):
            if assigned[start_idx]:
                continue
            cluster = []
            queue   = [start_idx]
            assigned[start_idx] = True
            while queue:
                idx    = queue.pop()
                px, py = points[idx]
                cluster.append(points[idx])
                gx = int(math.floor(px / cell))
                gy = int(math.floor(py / cell))
                for dgx in (-1, 0, 1):
                    for dgy in (-1, 0, 1):
                        for neighbour_idx in grid.get((gx + dgx, gy + dgy), []):
                            if assigned[neighbour_idx]:
                                continue
                            nx, ny = points[neighbour_idx]
                            if math.hypot(px - nx, py - ny) <= OBJ_CLUSTER_DIST:
                                assigned[neighbour_idx] = True
                                queue.append(neighbour_idx)
            if len(cluster) >= OBJ_MIN_CLUSTER_POINTS:
                clusters.append(cluster)
        return clusters
    def _cluster_centroid(self, cluster: List[Tuple[float, float]]) -> Tuple[float, float]:
        n = len(cluster)
        return (
            sum(p[0] for p in cluster) / n,
            sum(p[1] for p in cluster) / n,
        )
    def _world_to_body(self, wx: float, wy: float, robot_x: float,
                    robot_y: float, robot_yaw: float) -> Tuple[float, float]:
        dx  = wx - robot_x
        dy  = wy - robot_y
        fwd =  math.cos(robot_yaw) * dx + math.sin(robot_yaw) * dy
        lat = -math.sin(robot_yaw) * dx + math.cos(robot_yaw) * dy
        return fwd, lat
    def _detect_objects(self, scan: LaserScan, robot_x: float, robot_y: float,
                        robot_yaw: float, radius: float) -> List[Dict]:
        points   = self._scan_to_points(scan, robot_x, robot_y, robot_yaw, radius)
        clusters = self._cluster_points(points)
        objects  = []
        for cluster in clusters:
            cx, cy   = self._cluster_centroid(cluster)
            fwd, lat = self._world_to_body(cx, cy, robot_x, robot_y, robot_yaw)
            dist     = math.hypot(cx - robot_x, cy - robot_y)
            bearing  = math.degrees(math.atan2(lat, fwd))
            objects.append({
                'world_x':     cx,
                'world_y':     cy,
                'body_fwd':    fwd,
                'body_lat':    lat,
                'distance':    dist,
                'bearing_deg': bearing,
                'point_count': len(cluster),
            })
        objects.sort(key=lambda o: o['distance'])
        return objects
    # ==============================================================================
    # SECTION: Service Callbacks
    # ==============================================================================
    def _set_origin_cb(self, request, response):
        with self._lock:
            if self.position_state == PositionState.UNINITIALISED:
                response.success = False
                response.message = 'Cannot set origin - position not initialised.'
                return response
            origin_x   = self._est_x
            origin_y   = self._est_y
            origin_yaw = self._fused_yaw
            self._origin_x   = origin_x
            self._origin_y   = origin_y
            self._origin_yaw = origin_yaw
            self._update_public_position()
        response.success = True
        response.message = (
            f'Origin set: x={origin_x:.4f} y={origin_y:.4f} '
            f'yaw={math.degrees(origin_yaw):.2f}deg (reported position zeroed)'
        )
        self.get_logger().info(response.message)
        return response
    def _stop_move_cb(self):
        self._publish_cmd(0, 0, 0)
        
    def _set_reference_cb(self, request, response):
        with self._lock:
            state = self.position_state
            if state == PositionState.UNINITIALISED:
                response.success = False
                response.message = 'Position not initialised - no localisation source active.'
                return response
            if state == PositionState.DEGRADED:
                response.success = False
                response.message = ('Position DEGRADED - wait for RF2O or IMU '
                                    'before setting reference.')
                return response
            self._ref_x      = self._est_x
            self._ref_y      = self._est_y
            self._ref_yaw    = self._fused_yaw
            self._origin_x   = self._est_x
            self._origin_y   = self._est_y
            self._origin_yaw = self._fused_yaw
            self._update_public_position()
            ref_x_snap   = self._ref_x
            ref_y_snap   = self._ref_y
            ref_yaw_snap = self._ref_yaw
        response.success = True
        response.message = (
            f'Reference set: x={ref_x_snap:.3f} y={ref_y_snap:.3f} '
            f'yaw={math.degrees(ref_yaw_snap):.1f}°'
        )
        self.get_logger().info(response.message)
        return response
    def _publish_position(self) -> None:
        """
        20 Hz timer: publishes the current fused pose on /position (PoseStamped).
        Silently skips when position is UNINITIALISED.
        """
        with self._lock:
            state = self.position_state
            if state == PositionState.UNINITIALISED:
                return
            x   = self.position.x
            y   = self.position.y
            yaw = self.position.yaw
        msg = PoseStamped()
        msg.header.stamp    = self.get_clock().now().to_msg()
        msg.header.frame_id = 'map'
        msg.pose.position.x = x
        msg.pose.position.y = y
        msg.pose.position.z = 0.0
        half = yaw * 0.5
        msg.pose.orientation.x = 0.0
        msg.pose.orientation.y = 0.0
        msg.pose.orientation.z = math.sin(half)
        msg.pose.orientation.w = math.cos(half)
        self._position_pub.publish(msg)
    def _publish_objects(self) -> None:
        """10 Hz timer: publishes the current detected-obstacle list on /objects."""
        with self._lock:
            state      = self.position_state
            scan       = self._scan
            scan_stamp = self._scan_stamp
            now        = self._get_now_s()
            obj_fresh  = (now - self._objects_stamp) < SCAN_MAX_AGE_S
            scan_fresh = scan is not None and (now - scan_stamp) <= SCAN_MAX_AGE_S
            objects    = list(self._active_objects) if obj_fresh else []
        msg = String()
        if state == PositionState.UNINITIALISED:
            msg.data = 'UNINITIALISED'
        elif not scan_fresh:
            msg.data = 'NO_SCAN'
        elif not obj_fresh:
            msg.data = 'STALE'
        elif not objects:
            msg.data = 'NONE'
        else:
            lines = []
            for i, obj in enumerate(objects):
                lines.append(
                    f'[{i}] dist={obj["distance"]:.3f}m bear={obj["bearing_deg"]:+.1f}° '
                    f'fwd={obj["body_fwd"]:+.3f}m lat={obj["body_lat"]:+.3f}m '
                    f'pts={obj["point_count"]} '
                    f'world=({obj["world_x"]:.4f},{obj["world_y"]:.4f})'
                )
            msg.data = '\n'.join(lines)
        self._objects_pub.publish(msg)
    def _move_cb(self, request, response):
        with self._lock:
            state = self.position_state
            cur_x = self.position.x
            cur_y = self.position.y
        if state == PositionState.UNINITIALISED:
            response.success = False
            response.message = 'Cannot move: position not initialised.'
            return response
        goal_x    = float(request.data.x)
        goal_y    = float(request.data.y)
        move_dist = math.hypot(goal_x - cur_x, goal_y - cur_y)
        success = False
        try:
            success = self._run_move_loop(
                goal_x=goal_x,
                goal_y=goal_y,
                log_prefix='[service move]',
                owner='service',
            )
        finally:
            with self._lock:
                current_owner = self._move_owner
            if current_owner is None:
                self._publish_stop()
        response.success = success
        response.message = (
            f'Goal reached (requested dist={move_dist:.3f}m).'
            if success else
            'Move aborted or rejected - see log for details.'
        )
        self.get_logger().info(response.message)
        return response
# ==============================================================================
# SECTION: Node Entry Point
# ==============================================================================
def main(args=None):
    rclpy.init(args=args)
    node = GlobalRefNav()
    executor = MultiThreadedExecutor()
    executor.add_node(node)
    try:
        executor.spin()
    finally:
        node.destroy_node()
        rclpy.shutdown()
if __name__ == '__main__':
    main()
