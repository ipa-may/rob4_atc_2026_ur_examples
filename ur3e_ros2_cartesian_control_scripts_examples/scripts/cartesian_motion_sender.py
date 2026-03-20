#!/usr/bin/env python3
"""Send a simple pose target to the cartesian motion controller."""

import rclpy
from rclpy.duration import Duration
from geometry_msgs.msg import PoseStamped
from controller_utils import load_controller, switch_controller
from controller_manager_msgs.srv import SwitchController


# def ensure_cartesian_motion_controller(node) -> bool:
#     """Ensure the cartesian motion controller is loaded and active."""
#     if not load_controller(node, "cartesian_motion_controller"):
#         return False
#     return switch_controller(
#         node,
#         activate=["cartesian_motion_controller"],
#         deactivate=[
#             "scaled_joint_trajectory_controller",
#             "joint_trajectory_controller",
#         ],
#         strictness=SwitchController.Request.BEST_EFFORT,
#     )


def main() -> None:
    """Run the cartesian motion sender entrypoint."""
    rclpy.init()
    node = rclpy.create_node("cartesian_motion_sender")

    # if not ensure_cartesian_motion_controller(node):
    #     node.destroy_node()
    #     rclpy.shutdown()
    #     return

    publisher = node.create_publisher(
        PoseStamped,
        "/cartesian_motion_controller/target_frame",
        10,
    )

    target = PoseStamped()
    target.header.frame_id = "ur3e_base"
    # target.header.frame_id = "ur5e_base"
    target.pose.position.x = -0.0
    target.pose.position.y = -0.2
    target.pose.position.z = 0.6
    target.pose.orientation.w = 1.0

    # x: -0.10986858387784118
    # y: -0.23419889851047643
    # z: 0.9620386439617036

    node.get_logger().info("Publishing cartesian target frame... and spin")
    target.header.stamp = node.get_clock().now().to_msg()
    publisher.publish(target)

    # rclpy.spin_once(node, timeout_sec=0.2)
    rclpy.spin(node)
    node.get_logger().info("Published!")
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
