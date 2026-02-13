cmake_minimum_required(VERSION 3.8)
project(ur3e_ros2_cartesian_control_scripts_examples)

find_package(ament_cmake REQUIRED)

install(
  PROGRAMS
    scripts/controller_utils.py
    scripts/cartesian_motion_sender.py
    scripts/cartesian_compliance_sender.py
  DESTINATION lib/${PROJECT_NAME}
)

install(
  PROGRAMS
    scripts/cartesian_motion_sender.py
  DESTINATION lib/${PROJECT_NAME}
  RENAME cartesian_motion_sender
)

install(
  PROGRAMS
    scripts/cartesian_compliance_sender.py
  DESTINATION lib/${PROJECT_NAME}
  RENAME cartesian_compliance_sender
)

ament_package()
