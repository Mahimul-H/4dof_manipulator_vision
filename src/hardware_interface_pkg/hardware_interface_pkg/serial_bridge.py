#!/usr/bin/env python3
"""ROS 2 Serial Bridge Node for servo angle communication."""
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray
import serial
import time


class SerialBridgeNode(Node):
    """ROS 2 node that bridges servo angles to Arduino via serial."""

    def __init__(self):
        super().__init__('serial_bridge_node')

        # Declare ROS 2 parameters
        self.declare_parameter('serial_port', '/dev/ttyUSB0')
        self.declare_parameter('baud_rate', 115200)
        self.declare_parameter('send_interval', 1.75)  # seconds between sends

        # Get parameter values
        self.serial_port = self.get_parameter('serial_port').value
        self.baud_rate = self.get_parameter('baud_rate').value
        self.send_interval = self.get_parameter('send_interval').value

        # Initialize serial connection
        self.serial = None
        self._initialize_serial()

        # Rate limiting variables
        self.last_send_time = 0.0

        # Subscribe to servo angles
        self.subscription = self.create_subscription(
            Float32MultiArray,
            '/servo_angles',
            self.servo_angles_callback,
            10)

        self.get_logger().info(f'Serial Bridge node initialized')
        self.get_logger().info(f'  Serial Port: {self.serial_port}')
        self.get_logger().info(f'  Baud Rate: {self.baud_rate}')
        self.get_logger().info(f'  Send Interval: {self.send_interval}s')

    def _initialize_serial(self):
        """Initialize serial connection with error handling."""
        try:
            self.serial = serial.Serial(
                port=self.serial_port,
                baudrate=self.baud_rate,
                timeout=1.0
            )
            self.get_logger().info(
                f"Serial connection established: {self.serial_port} @ {self.baud_rate} baud")
            return True
        except serial.SerialException as e:
            self.get_logger().error(
                f"Failed to open serial port {self.serial_port}: {e}")
            self.get_logger().warn(
                "Node will continue running and attempt to reconnect on next data")
            self.serial = None
            return False

    def _try_reconnect(self):
        """Attempt to reconnect to serial port."""
        if self.serial is None:
            self.get_logger().info(
                f"Attempting to reconnect to {self.serial_port}...")
            return self._initialize_serial()
        return True

    def servo_angles_callback(self, msg):
        """Callback for servo angles subscriber.
        
        Receives Float32MultiArray with 4 servo angles and sends to Arduino.
        """
        if len(msg.data) < 4:
            self.get_logger().warn(
                f"Invalid message: expected 4 angles, got {len(msg.data)}")
            return

        # Extract servo angles (degrees) from Float32MultiArray
        angle_base = float(msg.data[0])
        angle_shoulder = float(msg.data[1])
        angle_elbow = float(msg.data[2])
        angle_wrist = float(msg.data[3])

        # Check rate limiting to prevent serial buffer overflow
        current_time = time.time()
        if current_time - self.last_send_time < self.send_interval:
            # Too soon, skip this command
            return

        # Round floats to nearest integers and format as CSV string
        # Example: [90.2, 45.9, 30.0, 90.0] → "90,46,30,90\n"
        angle_base_int = round(angle_base)
        angle_shoulder_int = round(angle_shoulder)
        angle_elbow_int = round(angle_elbow)
        angle_wrist_int = round(angle_wrist)
        
        # Append newline for Arduino protocol
        command = f"{angle_base_int},{angle_shoulder_int},{angle_elbow_int},{angle_wrist_int}\n"

        # Log the exact string being sent for debugging
        self.get_logger().debug(
            f"Servo angles (float): [{angle_base:.2f}, {angle_shoulder:.2f}, "
            f"{angle_elbow:.2f}, {angle_wrist:.2f}]")
        self.get_logger().info(
            f"Sending to Arduino: '{command.rstrip()}'")

        # Send to Arduino if serial is available
        if self.serial is not None and self.serial.is_open:
            try:
                self.serial.write(command.encode('utf-8'))
                self.last_send_time = current_time
                self.get_logger().info(
                    f"✓ Successfully sent: {command.rstrip()}")
            except serial.SerialException as e:
                self.get_logger().error(
                    f"Serial write failed: {type(e).__name__}: {e}")
                self.get_logger().warn("Marking serial as disconnected, will attempt reconnect on next message")
                self.serial = None
            except Exception as e:
                self.get_logger().error(
                    f"Unexpected error during serial write: {type(e).__name__}: {e}")
                self.serial = None
        else:
            # Serial not open, attempt to reconnect and retry
            self.get_logger().warn("Serial connection not available, attempting reconnect...")
            if self._try_reconnect() and self.serial is not None and self.serial.is_open:
                try:
                    self.serial.write(command.encode('utf-8'))
                    self.last_send_time = current_time
                    self.get_logger().info(
                        f"✓ Successfully sent after reconnect: {command.rstrip()}")
                except serial.SerialException as e:
                    self.get_logger().error(
                        f"Serial write failed after reconnect: {type(e).__name__}: {e}")
                    self.serial = None
                except Exception as e:
                    self.get_logger().error(
                        f"Unexpected error after reconnect: {type(e).__name__}: {e}")
                    self.serial = None
            else:
                self.get_logger().warn(
                    f"Could not reconnect to {self.serial_port}, command dropped")


def main(args=None):
    rclpy.init(args=args)
    node = SerialBridgeNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("Node stopping...")
    finally:
        if node.serial is not None and node.serial.is_open:
            node.serial.close()
            node.get_logger().info("Serial connection closed")
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
