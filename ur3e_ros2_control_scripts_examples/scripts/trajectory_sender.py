#!/usr/bin/env python3
"""Send a small two-point joint trajectory to the UR scaled trajectory controller."""

import rclpy
from rclpy.action import ActionClient
from rclpy.duration import Duration
from controller_manager_msgs.srv import SwitchController
from control_msgs.action import FollowJointTrajectory
from trajectory_msgs.msg import JointTrajectoryPoint
from .controller_utils import load_controller, switch_controller

# Container example ur3e
JOINT_NAMES: list[str] = [
    "ur3e_shoulder_pan_joint",
    "ur3e_shoulder_lift_joint",
    "ur3e_elbow_joint",
    "ur3e_wrist_1_joint",
    "ur3e_wrist_2_joint",
    "ur3e_wrist_3_joint",
]

# Real UR5e and UR3e
# JOINT_NAMES: list[str] = [
#     "shoulder_pan_joint",
#     "shoulder_lift_joint",
#     "elbow_joint",
#     "wrist_1_joint",
#     "wrist_2_joint",
#     "wrist_3_joint",
# ]


# JOINT_NAMES: list[str] = [
#     "ur5e_shoulder_pan_joint",
#     "ur5e_shoulder_lift_joint",
#     "ur5e_elbow_joint",
#     "ur5e_wrist_1_joint",
#     "ur5e_wrist_2_joint",
#     "ur5e_wrist_3_joint",
# ]


def build_goal() -> FollowJointTrajectory.Goal:
    """Build a sample joint trajectory goal."""
    goal: FollowJointTrajectory.Goal = FollowJointTrajectory.Goal()
    goal.trajectory.joint_names = JOINT_NAMES
    goal.trajectory.points = [
        JointTrajectoryPoint(
            positions=[0.785, -1.57, 0.785, 0.785, 0.785, 0.785],
            # positions=[0.0, -1.6, 2.0, 0.0, 0.2, 0.0],
            time_from_start=Duration(seconds=2).to_msg(),
        ),
        JointTrajectoryPoint(
            positions=[0.0, -1.57, 0.0, 0.0, 0.0, 0.0],
            # positions=[0.2, -1.6, 1.5, 0.2, -0.5, 0.0],
            time_from_start=Duration(seconds=4).to_msg(),
        ),
    ]
    return goal


def ensure_joint_trajectory_controller(node) -> bool:
    """Ensure the joint trajectory controller is loaded and active."""
    node.get_logger().info(
        "Deactivating cartesian controllers before enabling joint_trajectory_controller"
    )
    if not switch_controller(
        node,
        activate=[],
        deactivate=[
            "cartesian_motion_controller",
            "cartesian_compliance_controller",
            "cartesian_force_controller",
            "motion_control_handle",
        ],
        strictness=SwitchController.Request.BEST_EFFORT,
    ):
        node.get_logger().error("Failed to deactivate cartesian controllers")
        return False

    node.get_logger().info("Loading joint_trajectory_controller")
    if not load_controller(node, "joint_trajectory_controller"):
        return False

    node.get_logger().info(
        "Activating joint_trajectory_controller, deactivating scaled_joint_trajectory_controller"
    )
    result = switch_controller(
        node,
        activate=["joint_trajectory_controller"],
        deactivate=["scaled_joint_trajectory_controller"],
        strictness=SwitchController.Request.BEST_EFFORT,
    )
    if result:
        node.get_logger().info("Controller switch completed successfully")
    return result


def main() -> None:
    """Run the trajectory sender entrypoint."""
    rclpy.init()
    node = rclpy.create_node("trajectory_sender")
    # if not ensure_joint_trajectory_controller(node):
    #     node.destroy_node()
    #     rclpy.shutdown()
    #     return
    client = ActionClient(
        node,
        FollowJointTrajectory,
        "/joint_trajectory_controller/follow_joint_trajectory",
    )

    node.get_logger().info("Waiting for trajectory action server...")
    client.wait_for_server()
    node.get_logger().info("Server available, sending goal")

    goal: FollowJointTrajectory.Goal = build_goal()
    node.get_logger().info(f"Goal: {goal.trajectory.points[0].positions[0]}")

    send_future = client.send_goal_async(goal)
    rclpy.spin_until_future_complete(node, send_future)
    goal_handle = send_future.result()

    if goal_handle is None or not goal_handle.accepted:
        node.get_logger().error("Goal rejected by server")
        node.destroy_node()
        rclpy.shutdown()
        return

    node.get_logger().info("Goal accepted, waiting for result...")
    result_future = goal_handle.get_result_async()
    rclpy.spin_until_future_complete(node, result_future)
    result = result_future.result()

    if result is None:
        node.get_logger().error("Goal result unavailable")
    else:
        node.get_logger().info(f"Result: {result.result.error_code}")

    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
