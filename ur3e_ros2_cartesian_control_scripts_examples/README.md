# Cartesian Controllers on Universal Robots

A minimal setup to get the latest UR driver up and running with the `cartesian_controllers` for a *UR3e* robot.
Use this as a starting point to investigate basic mechanisms and to setup your own use case.

## Build

Build this package:
```sh
cd ~/ros2_ws
colcon build --packages-select ur3e_ros2_cartesian_control_scripts_examples
source install/setup.bash
```

If you build cartesian controllers from source, make sure they are in your workspace and rebuild the workspace.

## Run
Launch the UR control stack:
```sh
# With mock hardware
ros2 launch ur_atc_robot_cell_control start_robot.launch.py ur_type:=ur3e use_mock_hardware:=true

# With real robot
ros2 launch ur_atc_robot_cell_control start_robot.launch.py ur_type:=ur5e robot_ip:=<robot-ip>
```

Activate the correct controller


Send a simple cartesian target:
```sh
ros2 run ur3e_ros2_cartesian_control_scripts_examples cartesian_motion_sender_repeating
```

Send a set of waypoints to the controller:
```sh
ros2 run ur3e_ros2_cartesian_control_scripts_examples cartesian_motion_sender
``` 

Send a cartesian compliance target (pose + wrench):
```
ros2 run ur3e_ros2_cartesian_control_scripts_examples cartesian_compliance_sender
```

## Motion vs compliance controllers
The two cartesian controllers serve different purposes:

- `cartesian_motion_controller` tracks a target pose directly. It is suitable for free-space moves
  where you want to reach a position and orientation quickly.
- `cartesian_compliance_controller` tracks a target pose while also allowing compliant behavior
  via a target wrench. It is intended for contact tasks where you want to apply or regulate force
  while following a pose.

## Motion control handle
`motion_control_handle` is a helper controller used by the cartesian stack to manage shared state
and target interfaces for the cartesian controllers. You typically keep it loaded and inactive,
and only activate it when a cartesian controller explicitly requires it. It does not generate
motion on its own; it provides a common handle for motion-related inputs.
