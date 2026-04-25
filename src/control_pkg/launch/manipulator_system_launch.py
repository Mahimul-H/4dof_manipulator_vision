"""Launch file for complete 4-DOF manipulator system."""
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    """Generate launch description for complete manipulator system."""
    
    # Declare launch arguments
    declare_link1_length = DeclareLaunchArgument(
        'link1_length',
        default_value='0.15',
        description='Shoulder-to-elbow link length in meters'
    )
    
    declare_link2_length = DeclareLaunchArgument(
        'link2_length',
        default_value='0.15',
        description='Elbow-to-wrist link length in meters'
    )
    
    declare_serial_port = DeclareLaunchArgument(
        'serial_port',
        default_value='/dev/ttyUSB0',
        description='Serial port for Arduino communication'
    )
    
    declare_baud_rate = DeclareLaunchArgument(
        'baud_rate',
        default_value='115200',
        description='Serial port baud rate'
    )
    
    declare_angle_min = DeclareLaunchArgument(
        'angle_min_safe',
        default_value='0.0',
        description='Minimum safe servo angle in degrees'
    )
    
    declare_angle_max = DeclareLaunchArgument(
        'angle_max_safe',
        default_value='180.0',
        description='Maximum safe servo angle in degrees'
    )
    
    # Get package shares
    control_pkg_share = FindPackageShare('control_pkg')
    hardware_interface_pkg_share = FindPackageShare('hardware_interface_pkg')
    
    # Include controller launch file
    controller_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([control_pkg_share, 'launch', 'controller_launch.py'])
        ),
        launch_arguments={
            'link1_length': LaunchConfiguration('link1_length'),
            'link2_length': LaunchConfiguration('link2_length'),
            'angle_min_safe': LaunchConfiguration('angle_min_safe'),
            'angle_max_safe': LaunchConfiguration('angle_max_safe'),
        }.items()
    )
    
    # Include serial bridge launch file
    serial_bridge_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([hardware_interface_pkg_share, 'launch', 'serial_bridge_launch.py'])
        ),
        launch_arguments={
            'serial_port': LaunchConfiguration('serial_port'),
            'baud_rate': LaunchConfiguration('baud_rate'),
        }.items()
    )
    
    return LaunchDescription([
        declare_link1_length,
        declare_link2_length,
        declare_serial_port,
        declare_baud_rate,
        declare_angle_min,
        declare_angle_max,
        controller_launch,
        serial_bridge_launch,
    ])
