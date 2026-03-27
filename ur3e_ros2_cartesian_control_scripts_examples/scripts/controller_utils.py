"""Controller manager helper functions for cartesian scripts."""

import rclpy
from rclpy.duration import Duration
from rclpy.task import Future
from rclpy.client import Client
from controller_manager_msgs.srv import ListControllers, LoadController, SwitchController


def wait_for_service(node, client: Client, name: str) -> bool:
    """Wait for a service to be available."""
    if client.wait_for_service(timeout_sec=5.0):
        return True
    node.get_logger().error(f"{name} service not available")
    return False


def load_controller(node, controller_name: str) -> bool:
    """Load a controller through the controller manager."""
    client: Client = node.create_client(
        LoadController,
        "/controller_manager/load_controller",
    )
    if not wait_for_service(node, client, "Controller manager load"):
        return False

    request: LoadController.Request = LoadController.Request()
    request.name = controller_name
    future: Future = client.call_async(request)
    rclpy.spin_until_future_complete(node, future)
    result: LoadController.Response | None = future.result()
    if result is None:
        node.get_logger().error("Failed to call load controller service")
        return False
    if not result.ok:
        node.get_logger().warning(
            "Load controller reported failure, continuing to activation"
        )
    return True


def switch_controller(
    node,
    activate: list[str],
    deactivate: list[str],
    strictness: int,
) -> bool:
    """Switch controller states via the controller manager."""
    client: Client = node.create_client(
        SwitchController,
        "/controller_manager/switch_controller",
    )
    if not wait_for_service(node, client, "Controller manager switch"):
        return False

    request: SwitchController.Request = SwitchController.Request()
    request.activate_controllers = activate
    request.deactivate_controllers = deactivate
    request.strictness = strictness
    request.activate_asap = True
    request.timeout = Duration(seconds=5).to_msg()

    future: Future = client.call_async(request)
    rclpy.spin_until_future_complete(node, future)
    result: SwitchController.Response | None = future.result()
    if result is None:
        node.get_logger().error("Failed to call switch controller service")
        return False
    if not result.ok:
        node.get_logger().error("Controller switch reported failure")
        return False
    return True


def get_controller_state(node, controller_name: str) -> str | None:
    """Return the current lifecycle state for a controller."""
    client: Client = node.create_client(
        ListControllers,
        "/controller_manager/list_controllers",
    )
    if not wait_for_service(node, client, "Controller manager list"):
        return None

    request: ListControllers.Request = ListControllers.Request()
    future: Future = client.call_async(request)
    rclpy.spin_until_future_complete(node, future)
    result: ListControllers.Response | None = future.result()
    if result is None:
        node.get_logger().error("Failed to call list controllers service")
        return None

    for controller in result.controller:
        if controller.name == controller_name:
            return controller.state
    return None


def wait_for_controller_state(
    node,
    controller_name: str,
    expected_state: str,
    timeout_sec: float = 5.0,
) -> bool:
    """Wait until a controller reaches the expected lifecycle state."""
    deadline = node.get_clock().now().nanoseconds + int(timeout_sec * 1e9)
    while rclpy.ok() and node.get_clock().now().nanoseconds < deadline:
        state = get_controller_state(node, controller_name)
        if state == expected_state:
            return True
        rclpy.spin_once(node, timeout_sec=0.1)

    state = get_controller_state(node, controller_name)
    if state is None:
        node.get_logger().error(f"Controller '{controller_name}' not found")
    else:
        node.get_logger().error(
            f"Controller '{controller_name}' is '{state}', expected '{expected_state}'"
        )
    return False
