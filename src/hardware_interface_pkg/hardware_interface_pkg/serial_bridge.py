#!/usr/bin/env python3
"""ROS 2 Serial Bridge Node for Arduino communication."""
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray
import serial
import time


class SerialBridgeNode(Node):
    """ROS 2 node that bridges object coordinates to Arduino via serial."""

    def __init__(self):
        super().__init__('serial_bridge_node')

        # Declare parameters
        self.declare_parameter('serial_port', '/dev/ttyACM0')
        self.declare_parameter('baud_rate', 115200)
        self.declare_parameter('send_interval', 1.75)  # seconds between sends

        # Get parameter values
        self.serial_port = self.get_parameter('serial_port').value
        self.baud_rate = self.get_parameter('baud_rate').value
        self.send_interval = self.get_parameter('send_interval').value

        # Initialize serial connection
        self.serial = None
        try:
            self.serial = serial.Serial(
                port=self.serial_port,
                baudrate=self.baud_rate,
                timeout=1.0
            )
            self.get_logger().info(
                f"Serial connection established: {self.serial_port} at {self.baud_rate} baud")
        except serial.SerialException as e:
            self.get_logger().error(
                f"Failed to open serial port {self.serial_port}: {e}")
            self.get_logger().warn("Serial bridge will not send commands")

        # Rate limiting variables
        self.last_send_time = 0.0

        # Subscribe to object coordinates
        self.subscription = self.create_subscription(
            Float32MultiArray,
            '/object_coordinates',
            self.coordinates_callback,
            10)

        self.get_logger().info('Serial Bridge node initialized')

    def coordinates_callback(self, msg):
        """Callback for object coordinates subscriber."""
        if len(msg.data) < 3:
            self.get_logger().warn(
                f"Invalid message: expected 3 values, got {len(msg.data)}")
            return

        # Extract world coordinates
        world_x = float(msg.data[0])
        world_y = float(msg.data[1])
        world_z = float(msg.data[2])

        # Check rate limiting
        current_time = time.time()
        if current_time - self.last_send_time < self.send_interval:
            # Too soon, skip this command
            return

        # Format command for Arduino
        command = f"{world_x:.4f},{world_y:.4f},{world_z:.4f}\n"

        # Send to Arduino if serial is available
        if self.serial is not None:
            try:
                self.serial.write(command.encode())
                self.last_send_time = current_time
                self.get_logger().info(f"Sent to Arduino: {command.strip()}")
            except serial.SerialException as e:
                self.get_logger().error(f"Serial write failed: {e}")
        else:
            self.get_logger().warn("Serial not available, skipping command")


def main(args=None):
    rclpy.init(args=args)
    node = SerialBridgeNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("Node stopping...")
    finally:
        if node.serial is not None:
            node.serial.close()
            node.get_logger().info("Serial connection closed")
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
