#!/usr/bin/env python3
"""ROS 2 controller node for 4-DOF manipulator arm with PC-side IK."""
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray
import math
import numpy as np

from .ik_solver import IKSolver4DOF


class ControllerNode(Node):
    """ROS 2 node that subscribes to object coordinates, solves IK, and publishes servo angles."""

    def __init__(self):
        super().__init__('controller_node')

        # Declare ROS 2 parameters with defaults
        self.declare_parameter('link1_length', 0.15)  # L2 in meters (shoulder-elbow)
        self.declare_parameter('link2_length', 0.15)  # L3 in meters (elbow-wrist)
        self.declare_parameter('base_offset_y', 0.10)  # Camera offset from base
        self.declare_parameter('table_height', 0.25)  # Z coordinate of object plane
        self.declare_parameter('focal_length', 500.0)  # Camera focal length in pixels
        self.declare_parameter('center_x', 320.0)  # Principal point X
        self.declare_parameter('center_y', 240.0)  # Principal point Y
        self.declare_parameter('angle_min_safe', 0.0)  # Min safe angle (degrees)
        self.declare_parameter('angle_max_safe', 180.0)  # Max safe angle (degrees)

        # Camera intrinsics
        self.focal_length = self.get_parameter('focal_length').value
        self.center_x = self.get_parameter('center_x').value
        self.center_y = self.get_parameter('center_y').value
        self.table_height = self.get_parameter('table_height').value

        # Camera mounting offset
        self.camera_offset_y = self.get_parameter('base_offset_y').value

        # Safe zone constraints (degrees)
        self.angle_min_safe = self.get_parameter('angle_min_safe').value
        self.angle_max_safe = self.get_parameter('angle_max_safe').value

        # Initialize IK solver with arm parameters (link lengths in meters)
        # L1=0.1m (base height), L2=Link1, L3=Link2, L4=0.05m (wrist to tool)
        link1 = self.get_parameter('link1_length').value
        link2 = self.get_parameter('link2_length').value
        self.ik_solver = IKSolver4DOF(L1=0.1, L2=link1, L3=link2, L4=0.05)

        # Subscribe to pixel coordinates from vision
        self.subscription = self.create_subscription(
            Float32MultiArray,
            '/pixel_coordinates',
            self.coordinates_callback,
            10)

        # Publish servo angles for hardware interface
        self.servo_publisher = self.create_publisher(
            Float32MultiArray,
            '/servo_angles',
            10)

        self.get_logger().info('Controller node initialized - PC-side IK enabled')

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

            # Log joint angles in radians
            self.get_logger().info("[JOINT ANGLES - RADIANS]")
            self.get_logger().info(
                f"  θ1 (Base): {theta1:8.6f} rad  |  "
                f"θ2 (Shoulder): {theta2:8.6f} rad  |  "
                f"θ3 (Elbow): {theta3:8.6f} rad  |  "
                f"θ4 (Wrist): {theta4:8.6f} rad")

            # Log joint angles in degrees (before offsets and constraints)
            self.get_logger().info("[JOINT ANGLES - DEGREES (BEFORE ADJUSTMENT)]")
            self.get_logger().info(
                f"  θ1: {deg1:8.2f}°  |  "
                f"θ2: {deg2:8.2f}°  |  "
                f"θ3: {deg3:8.2f}°  |  "
                f"θ4: {deg4:8.2f}°")

            # Add 90-degree offset to shoulder (theta2) and elbow (theta3)
            # to ensure angles stay within 0-180° servo range
            deg2_offset = deg2 + 90.0
            deg3_offset = deg3 + 90.0

            self.get_logger().debug(
                f"Applied 90° offset: θ2 {deg2:.2f}° → {deg2_offset:.2f}°, "
                f"θ3 {deg3:.2f}° → {deg3_offset:.2f}°")

            # Apply hard constraints using numpy.clip to ensure [0, 180] range
            final_deg1 = float(np.clip(deg1, 0, 180))
            final_deg2 = float(np.clip(deg2_offset, 0, 180))
            final_deg3 = float(np.clip(deg3_offset, 0, 180))
            final_deg4 = float(np.clip(deg4, 0, 180))

            self.get_logger().info("[FINAL SERVO ANGLES - DEGREES (CLIPPED 0-180°)]")
            self.get_logger().info(
                f"  θ1 (Base):      {final_deg1:8.2f}°")
            self.get_logger().info(
                f"  θ2 (Shoulder):  {final_deg2:8.2f}°  (raw: {deg2:.2f}° + 90° offset)")
            self.get_logger().info(
                f"  θ3 (Elbow):     {final_deg3:8.2f}°  (raw: {deg3:.2f}° + 90° offset)")
            self.get_logger().info(
                f"  θ4 (Wrist):     {final_deg4:8.2f}°")

            # Convert to integers for Arduino command
            cmd_deg1 = int(round(final_deg1))
            cmd_deg2 = int(round(final_deg2))
            cmd_deg3 = int(round(final_deg3))
            cmd_deg4 = int(round(final_deg4))

            # Publish servo angles as Float32MultiArray (degrees, clipped)
            servo_msg = Float32MultiArray()
            servo_msg.data = [final_deg1, final_deg2, final_deg3, final_deg4]
            self.servo_publisher.publish(servo_msg)

            # Log Arduino command with final integer values
            self.get_logger().info("[ARDUINO COMMAND - INTEGER DEGREES (0-180)]")
            arduino_cmd = f"{cmd_deg1}, {cmd_deg2}, {cmd_deg3}, {cmd_deg4}"
            self.get_logger().info(f"  {arduino_cmd}")
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
