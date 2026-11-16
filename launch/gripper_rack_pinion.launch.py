#!/usr/bin/env python3
"""
Launch file for a rack-and-pinion gripper on one multi-turn STS motor.

The motor is homed against the gripper's open hard stop when the hardware interface activates
(see requires_homing in gripper_rack_pinion.urdf.xacro), so the gripper moves on startup.
The gripper_controller (joint trajectory controller) then commands the pinion angle in radians.

Example usage:
    ros2 launch sts_hardware_interface gripper_rack_pinion.launch.py serial_port:=/dev/ttyACM0
    ros2 launch sts_hardware_interface gripper_rack_pinion.launch.py use_mock:=true
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import Command, FindExecutable, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    """
    Generate launch description for the rack-and-pinion gripper.

    Returns
    -------
    LaunchDescription
        Complete launch configuration with all nodes and parameters

    """
    declared_arguments = [
        DeclareLaunchArgument(
            'serial_port', default_value='/dev/ttyACM0',
            description='Serial port for STS motor communication'),
        DeclareLaunchArgument(
            'motor_id', default_value='1', description='Motor ID (1-253)'),
        DeclareLaunchArgument(
            'baud_rate', default_value='1000000', description='Serial baud rate'),
        DeclareLaunchArgument(
            'use_mock', default_value='false',
            description='Use mock/simulation mode (no hardware required)'),
    ]

    robot_description_content = Command(
        [
            PathJoinSubstitution([FindExecutable(name='xacro')]),
            ' ',
            PathJoinSubstitution(
                [FindPackageShare('sts_hardware_interface'), 'config',
                 'gripper_rack_pinion.urdf.xacro']
            ),
            ' ', 'serial_port:=', LaunchConfiguration('serial_port'),
            ' ', 'motor_id:=', LaunchConfiguration('motor_id'),
            ' ', 'baud_rate:=', LaunchConfiguration('baud_rate'),
            ' ', 'use_mock:=', LaunchConfiguration('use_mock'),
        ]
    )
    robot_description = {
        'robot_description': ParameterValue(robot_description_content, value_type=str)
    }

    controller_config = PathJoinSubstitution(
        [FindPackageShare('sts_hardware_interface'), 'config',
         'gripper_rack_pinion_controllers.yaml']
    )

    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='both',
        parameters=[robot_description],
    )

    controller_manager_node = Node(
        package='controller_manager',
        executable='ros2_control_node',
        output='both',
        parameters=[robot_description, controller_config],
    )

    def spawner(name):
        return Node(
            package='controller_manager',
            executable='spawner',
            arguments=[name, '--controller-manager', '/controller_manager'],
        )

    nodes = [
        robot_state_publisher_node,
        controller_manager_node,
        spawner('joint_state_broadcaster'),
        spawner('state_interfaces_broadcaster'),
        spawner('gripper_controller'),
    ]

    return LaunchDescription(declared_arguments + nodes)
