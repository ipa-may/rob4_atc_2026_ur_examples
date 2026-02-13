from setuptools import setup

package_name = 'ur3e_ros2_control_scripts_examples'

setup(
    name=package_name,
    version='0.0.0',
    packages=['ur3e_ros2_control_scripts_examples'],
    package_dir={'ur3e_ros2_control_scripts_examples': 'scripts'},
    scripts=[
        'scripts/controller_utils.py',
        'scripts/trajectory_sender.py',
        'scripts/forward_velocity_sender.py',
    ],
    data_files=[
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='ros',
    maintainer_email='yasmine.makkaoui@ipa.fraunhofer.de',
    description='Helper scripts for controlling the UR robot cell.',
    license='BSD-3-Clause',
    extras_require={},
    entry_points={
        'console_scripts': [
            'send_trajectory = ur3e_ros2_control_scripts_examples.trajectory_sender:main',
            'send_velocity = ur3e_ros2_control_scripts_examples.forward_velocity_sender:main',
        ],
    },
)
