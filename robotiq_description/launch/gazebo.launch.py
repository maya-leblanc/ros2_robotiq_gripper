import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import ExecuteProcess, RegisterEventHandler
from launch.event_handlers import OnProcessExit
from launch_ros.actions import Node
import xacro

def generate_launch_description():

    # 1. Environment and Path Setup
    pkg = get_package_share_directory('robotiq_description')
    fruit_models_share = get_package_share_directory('fruit_models')
    
    fruit_models_dir = os.path.join(fruit_models_share, 'models')
    
    if 'GAZEBO_MODEL_PATH' in os.environ:
        os.environ['GAZEBO_MODEL_PATH'] += f":{fruit_models_dir}"
    else:
        os.environ['GAZEBO_MODEL_PATH'] = fruit_models_dir

    # Explicit path to the orange SDF file for the spawner
    orange_sdf_path = os.path.join(fruit_models_dir, 'orange', 'model.sdf')

    # 2. Robot Description (URDF/XACRO)
    xacro_file = os.path.join(pkg, 'urdf', 'robotiq_2f_85_gripper.urdf.xacro')
    robot_description = xacro.process_file(xacro_file, mappings={
        'sim_gazebo': 'true',
        'use_fake_hardware': 'true'
    }).toxml()

    # 3. Node Definitions
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[{'robot_description': robot_description}]
    )

    gazebo = ExecuteProcess(
        cmd=['gazebo', '--verbose', '-s', 'libgazebo_ros_factory.so'],
        output='screen'
    )

    spawn_entity = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        arguments=['-topic', 'robot_description',
                   '-entity', 'robotiq_gripper',
                   '-x', '0',
                   '-y', '0',
                   '-z', '0.05'],
        output='screen'
    )

    joint_state_broadcaster = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['joint_state_broadcaster'],
        output='screen'
    )

    spawn_orange = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        arguments=['-entity', 'orange',
                   '-file', orange_sdf_path,  # <--- Changed to use explicit file path
                   '-x', '0.15',
                   '-y', '0.0',
                   '-z', '0.05'],
        output='screen'
    )

    # 4. Launch Execution
    return LaunchDescription([
        robot_state_publisher,
        gazebo,
        spawn_orange,
        spawn_entity,
        RegisterEventHandler(
            event_handler=OnProcessExit(
                target_action=spawn_entity,
                on_exit=[joint_state_broadcaster]
            )
        )
    ])
