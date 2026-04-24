#!/usr/bin/env python3
"""ROS 2 controller node for 4-DOF manipulator arm."""
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray
import math

from .ik_solver import IKSolver4DOF


class ControllerNode(Node):
    """ROS 2 node that subscribes to object coordinates and computes joint angles."""

    def __init__(self):
        super().__init__('controller_node')

        # Camera intrinsics
        self.focal_length = 500.0
        self.center_x = 320.0
        self.center_y = 240.0
        self.table_height = 0.25  # meters (Z coordinate of object plane)

        # Camera mounting offset: 10cm behind robot base (along negative Y-axis)
        # This accounts for the camera's position relative to the robot base frame
        self.camera_offset_y = 0.10  # meters

        # Initialize IK solver with arm parameters (link lengths in meters)
        # L1=0.1m (base height), L2=0.15m, L3=0.15m, L4=0.05m
        # Total reach: 0.35m (matches 0.25m table height + 0.1m base offset)
        self.ik_solver = IKSolver4DOF(L1=0.1, L2=0.15, L3=0.15, L4=0.05)

        # Subscribe to object coordinates
        self.subscription = self.create_subscription(
            Float32MultiArray,
            '/object_coordinates',
            self.coordinates_callback,
            10)

        self.get_logger().info('Controller node initialized')

    def pixel_to_3d(self, x_pixel, y_pixel):
        """Convert 2D pixel coordinates to 3D world coordinates.

        Coordinate transformation:
        - Camera frame: looking down at the table (Z-axis down)
        - Robot base frame: X forward, Y left, Z up
        - Camera offset: 10cm behind (negative Y) robot base
        - Uses pinhole camera model with focal length and principal point
        """
        Z = self.table_height

        # Backproject using pinhole model (in camera frame)
        X_camera = (x_pixel - self.center_x) * Z / self.focal_length
        Y_camera = (y_pixel - self.center_y) * Z / self.focal_length

        # Transform from camera frame to robot base frame
        # Camera is mounted 10cm behind the robot base
        X_robot = X_camera
        Y_robot = Y_camera + self.camera_offset_y
        Z_robot = Z

        return X_robot, Y_robot, Z_robot

    def coordinates_callback(self, msg):
        """Callback for object coordinates subscriber."""
        if len(msg.data) < 3:
            self.get_logger().warn(
                f"Invalid message: expected 3 values, got {len(msg.data)}")
            return

        x_pixel = float(msg.data[0])
        y_pixel = float(msg.data[1])
        radius = float(msg.data[2])

        # Log raw pixel input
        self.get_logger().info("="*70)
        self.get_logger().info("[VISION INPUT - RAW PIXELS]")
        self.get_logger().info(
            f"  X_pixel: {x_pixel:8.2f}px  |  "
            f"Y_pixel: {y_pixel:8.2f}px  |  "
            f"Radius: {radius:8.2f}px")

        # Log camera parameters
        self.get_logger().info("[CAMERA PARAMETERS]")
        self.get_logger().info(
            f"  Focal Length: {self.focal_length:.1f}px  |  "
            f"Principal Point: ({self.center_x:.1f}, {self.center_y:.1f})  |  "
            f"Table Height: {self.table_height:.3f}m")
        self.get_logger().info(
            f"  Camera Offset (behind base): {self.camera_offset_y:.3f}m")

        # Convert pixel coordinates to 3D world coordinates
        x_3d, y_3d, z_3d = self.pixel_to_3d(x_pixel, y_pixel)

        # Log 3D conversion results
        self.get_logger().info("[3D WORLD COORDINATES - ROBOT BASE FRAME]")
        self.get_logger().info(
            f"  X: {x_3d:8.4f}m  |  Y: {y_3d:8.4f}m  |  Z: {z_3d:8.4f}m")
        self.get_logger().info(
            f"  Distance from base: {math.sqrt(x_3d**2 + y_3d**2 + z_3d**2):.4f}m")

        # Compute inverse kinematics
        angles = self.ik_solver.solve(x_3d, y_3d, z_3d, logger=self.get_logger())

        if angles is not None:
            theta1, theta2, theta3, theta4 = angles

            # Convert radians to degrees
            deg1 = math.degrees(theta1)
            deg2 = math.degrees(theta2)
            deg3 = math.degrees(theta3)
            deg4 = math.degrees(theta4)

            # Format for Arduino
            arduino_cmd = self.ik_solver.format_arduino_command(angles)

            # Log joint angles in radians
            self.get_logger().info("[JOINT ANGLES - RADIANS]")
            self.get_logger().info(
                f"  θ1: {theta1:8.6f} rad  |  "
                f"θ2: {theta2:8.6f} rad  |  "
                f"θ3: {theta3:8.6f} rad  |  "
                f"θ4: {theta4:8.6f} rad")

            # Log joint angles in degrees
            self.get_logger().info("[JOINT ANGLES - DEGREES]")
            self.get_logger().info(
                f"  θ1: {deg1:8.2f}°  |  "
                f"θ2: {deg2:8.2f}°  |  "
                f"θ3: {deg3:8.2f}°  |  "
                f"θ4: {deg4:8.2f}°")

            # Log Arduino command
            self.get_logger().info("[ARDUINO COMMAND]")
            self.get_logger().info(f"  {arduino_cmd.strip()}")
            self.get_logger().info("="*70)
        else:
            self.get_logger().error("="*70)
            self.get_logger().error("[IK SOLVER ERROR]")
            self.get_logger().error(
                f"  Target ({x_3d:.4f}m, {y_3d:.4f}m, {z_3d:.4f}m) is unreachable")
            self.get_logger().error("="*70)


def main(args=None):
    rclpy.init(args=args)
    node = ControllerNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("Node stopping...")
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
