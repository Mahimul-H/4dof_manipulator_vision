#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray
import cv2
import numpy as np


class ObjectDetector(Node):
    def __init__(self):
        super().__init__('object_detector')
        self.publisher_ = self.create_publisher(Float32MultiArray, '/object_coordinates', 10)

        # 1. Force V4L2 backend for Linux stability
        self.cap = cv2.VideoCapture(0, cv2.CAP_V4L2)

        if not self.cap.isOpened():
            self.get_logger().error("Failed to open camera at index 0")
        else:
            # Set resolution for better performance
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        # 2. FIXED: HSV for Red (Changed 1179 to 179)
        self.lower_hsv = np.array([0, 100, 100])
        self.upper_hsv = np.array([10, 255, 255])

        timer_period = 1.0 / 30.0  # 30 Hz
        self.timer = self.create_timer(timer_period, self.detect_callback)
        self.get_logger().info("ObjectDetector node started (30 Hz)")

    def detect_callback(self):
        ret, frame = self.cap.read()
        if not ret:
            self.get_logger().warn("Failed to capture frame")
            return

        # Pre-process: Blur to reduce high-frequency noise
        blurred = cv2.GaussianBlur(frame, (11, 11), 0)
        hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)

        # Thresholding
        mask = cv2.inRange(hsv, self.lower_hsv, self.upper_hsv)

        # Clean up the mask
        mask = cv2.erode(mask, None, iterations=2)
        mask = cv2.dilate(mask, None, iterations=2)

        contours, _ = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if contours:
            # Find the largest contour (the ball)
            c = max(contours, key=cv2.contourArea)
            ((x, y), radius) = cv2.minEnclosingCircle(c)

            if radius > 10:
                # Draw for visual feedback
                cv2.circle(frame, (int(x), int(y)), int(radius), (0, 255, 255), 2)
                cv2.circle(frame, (int(x), int(y)), 5, (0, 0, 255), -1)

                # Publish coordinates: [x, y, radius]
                msg = Float32MultiArray()
                msg.data = [float(x), float(y), float(radius)]
                self.publisher_.publish(msg)

        # Show the result
        cv2.imshow("Object Detector Feed", frame)
        cv2.waitKey(1)

    def stop_capture(self):
        """Separate cleanup method for safety."""
        if self.cap.isOpened():
            self.cap.release()
        cv2.destroyAllWindows()


def main(args=None):
    rclpy.init(args=args)
    node = ObjectDetector()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("Node stopping...")
    finally:
        # Ensure hardware is released no matter what
        node.stop_capture()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
