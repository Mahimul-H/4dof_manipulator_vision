"""Launch file for serial bridge node."""
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    """Generate launch description for serial bridge node."""
    
    # Declare launch arguments
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
    
    declare_send_interval = DeclareLaunchArgument(
        'send_interval',
        default_value='1.75',
        description='Minimum interval between sending commands in seconds'
    )
    
    # Create serial bridge node
    serial_bridge_node = Node(
        package='hardware_interface_pkg',
        executable='serial_bridge',
        name='serial_bridge_node',
        output='screen',
        parameters=[
            {'serial_port': LaunchConfiguration('serial_port')},
            {'baud_rate': LaunchConfiguration('baud_rate')},
            {'send_interval': LaunchConfiguration('send_interval')},
        ]
    )
    
    return LaunchDescription([
        declare_serial_port,
        declare_baud_rate,
        declare_send_interval,
        serial_bridge_node,
    ])
