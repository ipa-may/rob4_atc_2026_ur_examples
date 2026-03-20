#!/usr/bin/env python3
"""Publish a single target wrench command on /cartesian_force_controller/target_wrench."""

import rclpy
from geometry_msgs.msg import WrenchStamped


def main() -> None:
    """Run the cartesian force sender entrypoint."""
    rclpy.init()
    node = rclpy.create_node("cartesian_force_sender")

    publisher = node.create_publisher(WrenchStamped, "/cartesian_force_controller/target_wrench", 10)

    msg = WrenchStamped()
    msg.header.frame_id = "ur3e_tool0"
    msg.wrench.force.z = -3.0

    msg.header.stamp = node.get_clock().now().to_msg()
    publisher.publish(msg)
    node.get_logger().info("Published one /cartesian_force_controller/target_wrench message with force.z = 3.0")
    rclpy.spin_once(node, timeout_sec=0.1)

    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
