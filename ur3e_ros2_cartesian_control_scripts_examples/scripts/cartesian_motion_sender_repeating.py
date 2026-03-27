#!/usr/bin/env python3
"""Publish the same pose target repeatedly to the cartesian motion controller."""

import rclpy
from geometry_msgs.msg import PoseStamped


def main() -> None:
    """Run the repeating cartesian motion sender entrypoint."""
    rclpy.init()
    node = rclpy.create_node("cartesian_motion_sender_repeating")

    publisher = node.create_publisher(
        PoseStamped,
        "/cartesian_motion_controller/target_frame",
        10,
    )

    target = PoseStamped()
    target.header.frame_id = "ur5e_base"
    target.pose.position.x = -0.2
    target.pose.position.y = -0.23
    target.pose.position.z = 0.6
    target.pose.orientation.w = 1.0

    # cartesian_motion_controller ignores header.stamp and only checks frame_id and pose.
    publish_rate_hz = 10.0
    publish_duration_sec = 2.0
    wait_for_subscriber_sec = 2.0

    node.get_logger().info("Waiting for cartesian motion controller subscriber...")
    wait_deadline = node.get_clock().now().nanoseconds + int(wait_for_subscriber_sec * 1e9)
    while rclpy.ok() and node.get_clock().now().nanoseconds < wait_deadline:
        if publisher.get_subscription_count() > 0:
            break
        rclpy.spin_once(node, timeout_sec=0.1)

    if publisher.get_subscription_count() == 0:
        node.get_logger().warn(
            "No subscriber matched /cartesian_motion_controller/target_frame. "
            "Publishing anyway."
        )

    node.get_logger().info("Publishing cartesian target frame repeatedly...")
    end_time = node.get_clock().now().nanoseconds + int(publish_duration_sec * 1e9)
    rate = node.create_rate(publish_rate_hz)
    while rclpy.ok() and node.get_clock().now().nanoseconds < end_time:
        publisher.publish(target)
        rclpy.spin_once(node, timeout_sec=0.0)
        rate.sleep()

    node.get_logger().info("Stop publishing cartesian target frame.")
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
