#!/usr/bin/env python3
"""Reusable cartesian motion sender for the cartesian motion controller."""

import math
import time

import rclpy
from geometry_msgs.msg import PoseStamped, TransformStamped, TwistStamped

try:
    from .controller_utils import wait_for_controller_state
except ImportError:
    from controller_utils import wait_for_controller_state


class CartesianMotionSender:
    """Publish a short target burst for the cartesian motion controller."""

    def __init__(self) -> None:
        self._owns_rclpy_context = not rclpy.ok()
        if self._owns_rclpy_context:
            rclpy.init()

        self.node = rclpy.create_node("cartesian_motion_sender")
        self.controller_name = "cartesian_motion_controller"
        self.publisher = self.node.create_publisher(
            PoseStamped,
            "/cartesian_motion_controller/target_frame",
            10,
        )
        self.current_pose_subscription = self.node.create_subscription(
            PoseStamped,
            f"/{self.controller_name}/current_pose",
            self.current_pose_callback,
            10,
        )
        self.current_twist_subscription = self.node.create_subscription(
            TwistStamped,
            f"/{self.controller_name}/current_twist",
            self.current_twist_callback,
            10,
        )

        self.target_frame_id = "ur5e_base"
        self.target_x = -0.2
        self.target_y = -0.23
        self.target_z = 0.5
        self.target_qx = 0.0
        self.target_qy = 0.0
        self.target_qz = 0.0
        self.target_qw = 1.0

        self.wait_for_active_sec = 5.0
        self.wait_for_subscriber_sec = 2.0
        self.publish_rate_hz = 20.0
        self.publish_duration_sec = 1.0
        self.reach_timeout_sec = 10.0
        self.position_tolerance_m = 0.005
        self.orientation_tolerance_rad = 0.05
        self.linear_twist_tolerance = 0.01
        self.angular_twist_tolerance = 0.05

        self.current_pose: PoseStamped | None = None
        self.current_twist: TwistStamped | None = None
        self.active_target: PoseStamped | None = None
        self.reach_deadline_ns: int | None = None
        self.reset_state()

    def build_target(self) -> PoseStamped:
        """Build the target pose message from the configured attributes."""
        target = PoseStamped()
        target.header.frame_id = self.target_frame_id
        target.pose.position.x = self.target_x
        target.pose.position.y = self.target_y
        target.pose.position.z = self.target_z
        target.pose.orientation.x = self.target_qx
        target.pose.orientation.y = self.target_qy
        target.pose.orientation.z = self.target_qz
        target.pose.orientation.w = self.target_qw
        return target

    def set_target(
        self,
        frame_id: str,
        x: float,
        y: float,
        z: float,
        qx: float = 0.0,
        qy: float = 0.0,
        qz: float = 0.0,
        qw: float = 1.0,
    ) -> None:
        """Set the target pose attributes."""
        self.target_frame_id = frame_id
        self.target_x = x
        self.target_y = y
        self.target_z = z
        self.target_qx = qx
        self.target_qy = qy
        self.target_qz = qz
        self.target_qw = qw

    def set_target_pose(self, target_pose: PoseStamped) -> None:
        """Copy the target pose from a pose message."""
        self.set_target(
            frame_id=target_pose.header.frame_id,
            x=target_pose.pose.position.x,
            y=target_pose.pose.position.y,
            z=target_pose.pose.position.z,
            qx=target_pose.pose.orientation.x,
            qy=target_pose.pose.orientation.y,
            qz=target_pose.pose.orientation.z,
            qw=target_pose.pose.orientation.w,
        )

    def set_target_from_transform(self, transform: TransformStamped) -> None:
        """Copy the target pose from a transform lookup result."""
        self.set_target(
            frame_id=transform.header.frame_id,
            x=transform.transform.translation.x,
            y=transform.transform.translation.y,
            z=transform.transform.translation.z,
            qx=transform.transform.rotation.x,
            qy=transform.transform.rotation.y,
            qz=transform.transform.rotation.z,
            qw=transform.transform.rotation.w,
        )

    def reset_state(self) -> None:
        """Reset the execution state flags."""
        self.b_execute = False
        self.b_done = False
        self.b_busy = False
        self.b_error = False
        self.active_target = None
        self.reach_deadline_ns = None

    def current_pose_callback(self, message: PoseStamped) -> None:
        """Store current controller pose feedback."""
        self.current_pose = message
        self.update_done_state()

    def current_twist_callback(self, message: TwistStamped) -> None:
        """Store current controller twist feedback."""
        self.current_twist = message
        self.update_done_state()

    def wait_until_ready(self) -> bool:
        """Wait until the controller is active and the subscriber is discovered."""
        # cartesian_motion_controller ignores header.stamp and only checks frame_id and pose.
        self.node.get_logger().info(
            f"Waiting for '{self.controller_name}' to become active..."
        )
        if not wait_for_controller_state(
            self.node, self.controller_name, "active", self.wait_for_active_sec
        ):
            return False

        self.node.get_logger().info("Waiting for cartesian target subscriber discovery...")
        wait_deadline = (
            self.node.get_clock().now().nanoseconds + int(self.wait_for_subscriber_sec * 1e9)
        )
        while rclpy.ok() and self.node.get_clock().now().nanoseconds < wait_deadline:
            if self.publisher.get_subscription_count() > 0:
                break
            rclpy.spin_once(self.node, timeout_sec=0.1)

        if self.publisher.get_subscription_count() == 0:
            self.node.get_logger().warn(
                "No subscriber discovered on /cartesian_motion_controller/target_frame yet. "
                "Sending burst anyway."
            )
        return True

    def publish_target_burst(self) -> None:
        """Publish the configured target immediately for a short burst."""
        if self.active_target is None:
            self.active_target = self.build_target()
        self.node.get_logger().info("Publishing cartesian target frame burst...")
        end_time = (
            self.node.get_clock().now().nanoseconds + int(self.publish_duration_sec * 1e9)
        )
        publish_period_sec = 1.0 / self.publish_rate_hz
        while rclpy.ok() and self.node.get_clock().now().nanoseconds < end_time:
            self.publisher.publish(self.active_target)
            rclpy.spin_once(self.node, timeout_sec=0.0)
            time.sleep(publish_period_sec)

    def quaternion_error_rad(self) -> float:
        """Return the shortest angular difference between current and target orientation."""
        if self.active_target is None or self.current_pose is None:
            return math.inf

        target_q = self.active_target.pose.orientation
        current_q = self.current_pose.pose.orientation
        dot = (
            target_q.x * current_q.x
            + target_q.y * current_q.y
            + target_q.z * current_q.z
            + target_q.w * current_q.w
        )
        target_norm = math.sqrt(
            target_q.x**2 + target_q.y**2 + target_q.z**2 + target_q.w**2
        )
        current_norm = math.sqrt(
            current_q.x**2 + current_q.y**2 + current_q.z**2 + current_q.w**2
        )
        if target_norm == 0.0 or current_norm == 0.0:
            return math.inf

        dot /= target_norm * current_norm
        dot = max(-1.0, min(1.0, abs(dot)))
        return 2.0 * math.acos(dot)

    def position_error_m(self) -> float:
        """Return the Cartesian position error in meters."""
        if self.active_target is None or self.current_pose is None:
            return math.inf

        dx = self.active_target.pose.position.x - self.current_pose.pose.position.x
        dy = self.active_target.pose.position.y - self.current_pose.pose.position.y
        dz = self.active_target.pose.position.z - self.current_pose.pose.position.z
        return math.sqrt(dx * dx + dy * dy + dz * dz)

    def twist_norms(self) -> tuple[float, float]:
        """Return linear and angular twist norms."""
        if self.current_twist is None:
            return math.inf, math.inf

        linear = self.current_twist.twist.linear
        angular = self.current_twist.twist.angular
        linear_norm = math.sqrt(linear.x * linear.x + linear.y * linear.y + linear.z * linear.z)
        angular_norm = math.sqrt(
            angular.x * angular.x + angular.y * angular.y + angular.z * angular.z
        )
        return linear_norm, angular_norm

    def target_reached(self) -> bool:
        """Return True when pose error is small and the controller twist is near zero."""
        position_error = self.position_error_m()
        orientation_error = self.quaternion_error_rad()
        linear_twist_norm, angular_twist_norm = self.twist_norms()
        return (
            position_error <= self.position_tolerance_m
            and orientation_error <= self.orientation_tolerance_rad
            and linear_twist_norm <= self.linear_twist_tolerance
            and angular_twist_norm <= self.angular_twist_tolerance
        )

    def update_done_state(self) -> None:
        """Update done/error flags from controller feedback."""
        if not self.b_busy:
            return

        now_ns = self.node.get_clock().now().nanoseconds
        if self.reach_deadline_ns is not None and now_ns > self.reach_deadline_ns:
            self.b_busy = False
            self.b_error = True
            self.node.get_logger().error("Timed out waiting for cartesian target to be reached.")
            return

        if self.target_reached():
            self.b_busy = False
            self.b_done = True
            self.b_error = False
            self.node.get_logger().info("Cartesian target reached.")

    def spin_once(self, timeout_sec: float = 0.05) -> None:
        """Process one executor cycle and refresh the done/error flags."""
        rclpy.spin_once(self.node, timeout_sec=timeout_sec)
        self.update_done_state()

    def run(self, wait_for_ready: bool = False) -> None:
        """Publish a short target burst and wait for feedback to report target convergence."""
        self.reset_state()
        self.b_execute = True
        self.b_busy = True
        self.active_target = self.build_target()
        self.reach_deadline_ns = (
            self.node.get_clock().now().nanoseconds + int(self.reach_timeout_sec * 1e9)
        )

        if wait_for_ready and not self.wait_until_ready():
            self.b_busy = False
            self.b_error = True
            return

        self.publish_target_burst()
        self.node.get_logger().info("Published target burst, waiting for feedback.")

    def close(self) -> None:
        """Destroy the node and shut ROS down when this object created the context."""
        self.node.destroy_node()
        if self._owns_rclpy_context and rclpy.ok():
            rclpy.shutdown()
