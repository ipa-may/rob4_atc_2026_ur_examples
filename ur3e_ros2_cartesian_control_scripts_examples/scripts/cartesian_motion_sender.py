#!/usr/bin/env python3
"""Send simple pose targets to the cartesian motion controller."""

try:
    from .cartesian_motion_sender_lib import CartesianMotionSender
except ImportError:
    from cartesian_motion_sender_lib import CartesianMotionSender


def main() -> None:
    """Run the cartesian motion sender entrypoint."""
    sender = CartesianMotionSender()

    try:
        sender.set_target("ur5e_base", -0.2, -0.23, 0.65)
        sender.run()
        while not sender.b_done and not sender.b_error:
            sender.spin_once()
        if sender.b_error:
            sender.node.get_logger().error("Failed to reach first target.")
            return

        sender.set_target("ur5e_base", -0.15, -0.20, 0.45)
        sender.run()
        while not sender.b_done and not sender.b_error:
            sender.spin_once()
        if sender.b_error:
            sender.node.get_logger().error("Failed to reach second target.")
            return
    finally:
        sender.close()


if __name__ == "__main__":
    main()
