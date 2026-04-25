"""Launch file for controller node with IK solver."""
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    """Generate launch description for controller node."""
    
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
    
    declare_focal_length = DeclareLaunchArgument(
        'focal_length',
        default_value='500.0',
        description='Camera focal length in pixels'
    )
    
    declare_center_x = DeclareLaunchArgument(
        'center_x',
        default_value='320.0',
        description='Camera principal point X in pixels'
    )
    
    declare_center_y = DeclareLaunchArgument(
        'center_y',
        default_value='240.0',
        description='Camera principal point Y in pixels'
    )
    
    declare_table_height = DeclareLaunchArgument(
        'table_height',
        default_value='0.25',
        description='Table height (Z coordinate) in meters'
    )
    
    declare_base_offset_y = DeclareLaunchArgument(
        'base_offset_y',
        default_value='0.10',
        description='Camera offset from robot base in meters'
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
    
    # Create controller node
    controller_node = Node(
        package='control_pkg',
        executable='controller',
        name='controller_node',
        output='screen',
        parameters=[
            {'link1_length': LaunchConfiguration('link1_length')},
            {'link2_length': LaunchConfiguration('link2_length')},
            {'focal_length': LaunchConfiguration('focal_length')},
            {'center_x': LaunchConfiguration('center_x')},
            {'center_y': LaunchConfiguration('center_y')},
            {'table_height': LaunchConfiguration('table_height')},
            {'base_offset_y': LaunchConfiguration('base_offset_y')},
            {'angle_min_safe': LaunchConfiguration('angle_min_safe')},
            {'angle_max_safe': LaunchConfiguration('angle_max_safe')},
        ]
    )
    
    return LaunchDescription([
        declare_link1_length,
        declare_link2_length,
        declare_focal_length,
        declare_center_x,
        declare_center_y,
        declare_table_height,
        declare_base_offset_y,
        declare_angle_min,
        declare_angle_max,
        controller_node,
    ])
