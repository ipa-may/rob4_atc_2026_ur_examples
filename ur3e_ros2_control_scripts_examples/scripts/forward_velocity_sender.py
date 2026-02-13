#!/usr/bin/env python3
"""Send a short joint velocity command using the forward velocity controller."""

import rclpy
from rclpy.duration import Duration
from rclpy.node import Node
from rclpy.time import Time
from rclpy.publisher import Publisher
from rclpy.timer import Rate
from std_msgs.msg import Float64MultiArray
from controller_manager_msgs.srv import SwitchController
from .controller_utils import load_controller, switch_controller


JOINT_NAMES: list[str] = [
    "ur3e_shoulder_pan_joint",
    "ur3e_shoulder_lift_joint",
    "ur3e_elbow_joint",
    "ur3e_wrist_1_joint",
    "ur3e_wrist_2_joint",
    "ur3e_wrist_3_joint",
]


def switch_to_velocity_controller(node: Node) -> bool:
    """Load and activate the forward velocity controller."""
    if not load_controller(node, "forward_velocity_controller"):
        return False
    return switch_controller(
        node,
        activate=["forward_velocity_controller"],
        deactivate=[],
        strictness=SwitchController.Request.BEST_EFFORT,
    )


def main() -> None:
    """Run the forward velocity sender entrypoint."""
    rclpy.init()
    node = rclpy.create_node("forward_velocity_sender")

    if not switch_to_velocity_controller(node):
        node.destroy_node()
        rclpy.shutdown()
        return

    publisher: Publisher = node.create_publisher(
        Float64MultiArray,
        "/forward_velocity_controller/commands",
        10,
    )

    node.get_logger().info("Publishing joint velocity commands...")
    message: Float64MultiArray = Float64MultiArray()
    message.data = [0.2, -0.1, 0.1, 0.0, 0.0, 0.0]
    stop_message: Float64MultiArray = Float64MultiArray()
    stop_message.data = [0.0] * len(JOINT_NAMES)

    start_time: Time = node.get_clock().now()
    duration: Duration = Duration(seconds=2.0)
    rate: Rate = node.create_rate(10.0)
    while rclpy.ok() and (node.get_clock().now() - start_time) < duration:
        publisher.publish(message)
        rate.sleep()

    publisher.publish(stop_message)
    node.get_logger().info("Velocity command complete")

    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
