#!/usr/bin/env bash

set -euo pipefail # exit (exit immediately if a command fails), use (treat use of an unset variable as an error)

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
workspace_root="$(realpath "${script_dir}/../..")"

echo "Workspace: ${workspace_root}"
cd "${workspace_root}"

if [[ -n "${ROS_DISTRO:-}" && -f "/opt/ros/${ROS_DISTRO}/setup.bash" ]]; then
    # Make sure colcon sees the base ROS environment when the caller has not sourced it yet.
    # shellcheck disable=SC1090
    set +u
    source "/opt/ros/${ROS_DISTRO}/setup.bash"
    set -u
fi

echo "Building up to ur_atc_robot_cell_control..."
colcon build --packages-up-to ur_atc_robot_cell_control

echo "Building Cartesian Controllers packages in Release mode..."
colcon build \
    --packages-skip cartesian_controller_simulation cartesian_controller_tests \
    --cmake-args -DCMAKE_BUILD_TYPE=Release

echo "Building ur3e_ros2_cartesian_control_scripts_examples..."
colcon build --packages-select ur3e_ros2_cartesian_control_scripts_examples

echo "Building ur3e_ros2_control_scripts_examples..."
colcon build --packages-select ur3e_ros2_control_scripts_examples

if [[ -f "${workspace_root}/install/setup.bash" ]]; then
    # shellcheck disable=SC1090
    set +u
    source "${workspace_root}/install/setup.bash"
    set -u
    echo "Sourced ${workspace_root}/install/setup.bash"
fi
