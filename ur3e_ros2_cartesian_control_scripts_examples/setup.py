from glob import glob
from setuptools import setup


package_name = "ur3e_ros2_cartesian_control_scripts_examples"


setup(
    name=package_name,
    version="0.0.0",
    packages=[package_name],
    package_dir={package_name: "scripts"},
    data_files=[
        (
            "share/ament_index/resource_index/packages",
            [f"resource/{package_name}"],
        ),
        (f"share/{package_name}", ["package.xml"]),
        (f"share/{package_name}/config", glob("config/*")),
        (f"share/{package_name}/positions", glob("positions/*")),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="Stefan Scherzinger",
    maintainer_email="scherzin@fzi.de",
    description="An easy-to-start configuration for cartesian_controllers on Universal Robots",
    license="BSD-3-Clause",
    entry_points={
        "console_scripts": [
            "cartesian_motion_sender = ur3e_ros2_cartesian_control_scripts_examples.cartesian_motion_sender:main",
            "cartesian_motion_sender_repeating = ur3e_ros2_cartesian_control_scripts_examples.cartesian_motion_sender_repeating:main",
            "cartesian_compliance_sender = ur3e_ros2_cartesian_control_scripts_examples.cartesian_compliance_sender:main",
            "cartesian_servo = ur3e_ros2_cartesian_control_scripts_examples.cartesian_servo:main",
            "cartesian_force_sender = ur3e_ros2_cartesian_control_scripts_examples.cartesian_force_sender:main",
        ],
    },
)
