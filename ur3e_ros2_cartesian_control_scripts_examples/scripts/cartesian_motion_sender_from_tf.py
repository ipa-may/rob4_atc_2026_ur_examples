#!/usr/bin/env python3
"""Lookup a TF transform and send it as a cartesian motion target."""

import argparse

import rclpy
from rclpy.duration import Duration
from rclpy.time import Time
from tf2_ros import Buffer, TransformException, TransformListener

try:
    from .cartesian_motion_sender_lib import CartesianMotionSender
except ImportError:
    from cartesian_motion_sender_lib import CartesianMotionSender


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description=(
            "Send the transform from source_frame into target_frame as the first "
            "cartesian target. Defaults match: ros2 run tf2_ros tf2_echo ur3e_base pose_1"
        )
    )
    parser.add_argument(
        "target_frame",
        nargs="?",
        default="ur3e_base",
        help="Target frame used in tf_buffer.lookup_transform(target_frame, source_frame, time).",
    )
    parser.add_argument(
        "source_frame",
        nargs="?",
        default="pose_1",
        help="Source frame used in tf_buffer.lookup_transform(target_frame, source_frame, time).",
    )
    parser.add_argument(
        "--tf-timeout",
        type=float,
        default=5.0,
        help="Seconds to wait for the TF lookup.",
    )
    parser.add_argument(
        "--wait-for-ready",
        action="store_true",
        help="Wait for the cartesian motion controller to report active before sending.",
    )
    return parser.parse_args()


def main() -> None:
    """Run the TF-driven cartesian motion sender entrypoint."""
    args = parse_args()
    rclpy.init()

    tf_node = rclpy.create_node("cartesian_motion_sender_from_tf")
    tf_buffer = Buffer()
    tf_listener = TransformListener(tf_buffer, tf_node, spin_thread=True)
    sender = CartesianMotionSender()

    try:
        sender.node.get_logger().info(
            "Looking up transform with lookup_transform("
            f"target='{args.target_frame}', source='{args.source_frame}', time=latest)."
        )
        transform = tf_buffer.lookup_transform(
            args.target_frame,
            args.source_frame,
            Time(),
            timeout=Duration(seconds=args.tf_timeout),
        )
        sender.set_target_from_transform(transform)
        sender.node.get_logger().info(
            "First target pose loaded from TF: "
            f"{args.target_frame} <- {args.source_frame}"
        )

        sender.run(wait_for_ready=args.wait_for_ready)
        while not sender.b_done and not sender.b_error:
            sender.spin_once()
        if sender.b_error:
            sender.node.get_logger().error("Failed to reach TF-derived target.")
    except TransformException as exc:
        sender.node.get_logger().error(
            f"Failed to lookup transform {args.target_frame} <- {args.source_frame}: {exc}"
        )
    finally:
        sender.close()
        del tf_listener
        tf_node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
