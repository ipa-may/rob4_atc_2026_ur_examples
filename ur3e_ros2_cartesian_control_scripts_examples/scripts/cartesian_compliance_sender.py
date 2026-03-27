#!/usr/bin/env python3
"""Send a simple pose and wrench target to the cartesian compliance controller."""

import rclpy
from rclpy.duration import Duration
from geometry_msgs.msg import PoseStamped, WrenchStamped
from controller_manager_msgs.srv import SwitchController

try:
    from .controller_utils import load_controller, switch_controller
except ImportError:
    from controller_utils import load_controller, switch_controller


# def ensure_cartesian_compliance_controller(node) -> bool:
#     """Ensure the cartesian compliance controller is loaded and active."""
#     if not load_controller(node, "cartesian_compliance_controller"):
#         return False
#     return switch_controller(
#         node,
#         activate=["cartesian_compliance_controller"],
#         deactivate=[
#             "scaled_joint_trajectory_controller",
#             "joint_trajectory_controller",
#         ],
#         strictness=SwitchController.Request.BEST_EFFORT,
#     )


def main() -> None:
    """Run the cartesian compliance sender entrypoint."""
    rclpy.init()
    node = rclpy.create_node("cartesian_compliance_sender")

    # if not ensure_cartesian_compliance_controller(node):
    #     node.destroy_node()
    #     rclpy.shutdown()
    #     return

    pose_publisher = node.create_publisher(
        PoseStamped,
        "/cartesian_compliance_controller/target_frame",
        10,
    )
    wrench_publisher = node.create_publisher(
        WrenchStamped,
        "/cartesian_compliance_controller/target_wrench",
        10,
    )

    target_pose = PoseStamped()
    target_pose.header.frame_id = "ur3e_base"
    target_pose.pose.position.x = 0.4
    target_pose.pose.position.y = 0.0
    target_pose.pose.position.z = 0.4
    target_pose.pose.orientation.w = 1.0

    target_wrench = WrenchStamped()
    target_wrench.header.frame_id = "ur3e_tool0"

    node.get_logger().info("Publishing cartesian compliance targets...")
    now = node.get_clock().now().to_msg()
    target_pose.header.stamp = now
    target_wrench.header.stamp = now
    pose_publisher.publish(target_pose)
    wrench_publisher.publish(target_wrench)

    rclpy.spin_once(node, timeout_sec=0.2)
    node.get_logger().info("Cartesian compliance command complete")
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
