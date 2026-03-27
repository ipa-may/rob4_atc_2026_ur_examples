#!/usr/bin/env python3
"""Publish the same pose target repeatedly to the cartesian motion controller."""

import time

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

    node.get_logger().info("Waiting for cartesian motion controller subscriber...")
    
    
    node.get_logger().info("Publishing cartesian target frame repeatedly...")
    node.get_logger().info(
        f"Publishing for {publish_duration_sec:.1f} s at {publish_rate_hz:.1f} Hz"
    )
    end_time_sec = time.monotonic() + publish_duration_sec
    publish_period_sec = 1.0 / publish_rate_hz
    while rclpy.ok() and time.monotonic() < end_time_sec:
        publisher.publish(target)
        rclpy.spin_once(node, timeout_sec=0.0)
        time.sleep(publish_period_sec)

    node.get_logger().info("Stop publishing cartesian target frame.")
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
