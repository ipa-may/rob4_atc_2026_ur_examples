#!/usr/bin/env python3
"""Keyboard-driven cartesian servo for the motion controller."""

import select
import sys
import termios
import tty
from typing import Any, Optional

import rclpy
from rclpy.duration import Duration
from geometry_msgs.msg import PoseStamped
from tf2_ros import Buffer, TransformException, TransformListener


class CartesianServo:
    """Publish cartesian pose targets based on keyboard input."""

    def __init__(self) -> None:
        rclpy.init()
        self.node = rclpy.create_node("cartesian_servo")
        self.start_wait_timeout_sec: float = 3.0
        self.publisher = self.node.create_publisher(
            PoseStamped,
            "/cartesian_motion_controller/target_frame",
            10,
        )
        self.tf_buffer: Buffer = Buffer()
        self.tf_listener: TransformListener = TransformListener(
            self.tf_buffer, self.node
        )
        # ur3e default parameters
        self.step_size: float = 0.005
        self.base_frame: str = (
            self.node.declare_parameter("base_frame", "ur3e_base")
            .get_parameter_value()
            .string_value
        )
        self.tool_frame: str = (
            self.node.declare_parameter("tool_frame", "ur3e_tool0")
            .get_parameter_value()
            .string_value
        )
        # ur5e default parameters
        # self.step_size: float = 0.005
        # self.base_frame: str = (
        #     self.node.declare_parameter("base_frame", "ur5e_base")
        #     .get_parameter_value()
        #     .string_value
        # )
        # self.tool_frame: str = (
        #     self.node.declare_parameter("tool_frame", "ur5e_tool0")
        #     .get_parameter_value()
        #     .string_value
        # )
        self.key_x_positive: str = self._declare_key_parameter("key_x_positive", "q")
        self.key_x_negative: str = self._declare_key_parameter("key_x_negative", "a")
        self.key_y_positive: str = self._declare_key_parameter("key_y_positive", "w")
        self.key_y_negative: str = self._declare_key_parameter("key_y_negative", "s")
        self.key_z_positive: str = self._declare_key_parameter("key_z_positive", "e")
        self.key_z_negative: str = self._declare_key_parameter("key_z_negative", "d")
        self.key_exit: str = self._declare_key_parameter("key_exit", "x")

        self.target: PoseStamped = PoseStamped()
        self.target.header.frame_id = self.base_frame
        self.target.pose.position.x = -0.463
        self.target.pose.position.y = -0.26
        self.target.pose.position.z = 0.379
        self.target.pose.orientation.w = 1.0

        self._term_settings: list[Any] = termios.tcgetattr(sys.stdin)

    def run(self) -> None:
        """Run the keyboard loop and publish pose updates."""
        self._initialize_from_forward_kinematics()
        self.node.get_logger().info(
            "Keyboard servo started. "
            f"X: {self.key_x_positive}/{self.key_x_negative}, "
            f"Y: {self.key_y_positive}/{self.key_y_negative}, "
            f"Z: {self.key_z_positive}/{self.key_z_negative}, "
            f"press '{self.key_exit}' to exit."
        )

        try:
            tty.setcbreak(sys.stdin.fileno())
            self._publish_target()

            while rclpy.ok():
                rclpy.spin_once(self.node, timeout_sec=0.01)
                key = self._read_key(timeout=0.1)
                if key is None:
                    continue

                if key == self.key_x_positive:
                    self.target.pose.position.x += self.step_size
                    self._publish_target()
                elif key == self.key_x_negative:
                    self.target.pose.position.x -= self.step_size
                    self._publish_target()
                elif key == self.key_y_positive:
                    self.target.pose.position.y += self.step_size
                    self._publish_target()
                elif key == self.key_y_negative:
                    self.target.pose.position.y -= self.step_size
                    self._publish_target()
                elif key == self.key_z_positive:
                    self.target.pose.position.z += self.step_size
                    self._publish_target()
                elif key == self.key_z_negative:
                    self.target.pose.position.z -= self.step_size
                    self._publish_target()
                elif key == self.key_exit:
                    break
        finally:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self._term_settings)
            self.node.destroy_node()
            rclpy.shutdown()

    def _read_key(self, timeout: float = 0.0) -> Optional[str]:
        readable, _, _ = select.select([sys.stdin], [], [], timeout)
        if not readable:
            return None
        return sys.stdin.read(1)

    def _publish_target(self) -> None:
        self.target.header.stamp = self.node.get_clock().now().to_msg()
        self.publisher.publish(self.target)
        self.node.get_logger().info(
            f"Published target X: {self.target.pose.position.x:.3f}"
        )

    def _declare_key_parameter(self, name: str, default: str) -> str:
        value = (
            self.node.declare_parameter(name, default).get_parameter_value().string_value
        )
        if len(value) != 1:
            self.node.get_logger().warn(
                f"Parameter '{name}' must be one character. Using '{default}'."
            )
            return default
        return value

    def _initialize_from_forward_kinematics(self) -> None:
        timeout = Duration(seconds=self.start_wait_timeout_sec)
        start_time = self.node.get_clock().now()
        self.node.get_logger().info(
            f"Waiting for FK pose from TF: {self.base_frame} -> {self.tool_frame}"
        )

        while rclpy.ok() and (self.node.get_clock().now() - start_time) < timeout:
            rclpy.spin_once(self.node, timeout_sec=0.1)
            try:
                transform = self.tf_buffer.lookup_transform(
                    self.base_frame,
                    self.tool_frame,
                    rclpy.time.Time(),
                )
                self.target.header.frame_id = self.base_frame
                self.target.pose.position.x = transform.transform.translation.x
                self.target.pose.position.y = transform.transform.translation.y
                self.target.pose.position.z = transform.transform.translation.z
                self.target.pose.orientation = transform.transform.rotation
                self.node.get_logger().info("Initialized start pose from FK/TF.")
                return
            except TransformException:
                continue

        self.node.get_logger().warn(
            "Could not get FK pose from TF before timeout. Using default start pose."
        )


def main() -> None:
    """Run the cartesian servo entrypoint."""
    servo = CartesianServo()
    servo.run()


if __name__ == "__main__":
    main()
