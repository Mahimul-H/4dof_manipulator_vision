#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
import cv2
import numpy as np


def nothing(x):
    pass


class ColorCalibrator(Node):
    def __init__(self):
        super().__init__('color_calibrator')

        # Using index 0 - confirmed working camera
        self.cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
        if not self.cap.isOpened():
            self.get_logger().error("Failed to open camera at index 0")

        self.get_logger().info("ColorCalibrator node initialized")

    def run_calibration(self):
        """Run the interactive color calibration tool."""
        cv2.namedWindow("Trackbars")
        cv2.createTrackbar("L-H", "Trackbars", 0, 179, nothing)
        cv2.createTrackbar("L-S", "Trackbars", 0, 255, nothing)
        cv2.createTrackbar("L-V", "Trackbars", 0, 255, nothing)
        cv2.createTrackbar("U-H", "Trackbars", 179, 179, nothing)
        cv2.createTrackbar("U-S", "Trackbars", 255, 255, nothing)
        cv2.createTrackbar("U-V", "Trackbars", 255, 255, nothing)

        self.get_logger().info("Adjust sliders until your object is WHITE and background is BLACK.")
        self.get_logger().info("Press 'q' to exit and save values.")

        while True:
            ret, frame = self.cap.read()
            if not ret:
                self.get_logger().error("Failed to capture frame")
                break

            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

            l_h = cv2.getTrackbarPos("L-H", "Trackbars")
            l_s = cv2.getTrackbarPos("L-S", "Trackbars")
            l_v = cv2.getTrackbarPos("L-V", "Trackbars")
            u_h = cv2.getTrackbarPos("U-H", "Trackbars")
            u_s = cv2.getTrackbarPos("U-S", "Trackbars")
            u_v = cv2.getTrackbarPos("U-V", "Trackbars")

            lower = np.array([l_h, l_s, l_v])
            upper = np.array([u_h, u_s, u_v])

            mask = cv2.inRange(hsv, lower, upper)
            result = cv2.bitwise_and(frame, frame, mask=mask)

            cv2.imshow("Frame", frame)
            cv2.imshow("Mask", mask)
            cv2.imshow("Result", result)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                print(f"Final HSV Values: Lower [{l_h}, {l_s}, {l_v}], Upper [{u_h}, {u_s}, {u_v}]")
                self.get_logger().info(f"Final HSV Values: Lower [{l_h}, {l_s}, {l_v}], Upper [{u_h}, {u_s}, {u_v}]")
                break

    def destroy_node(self):
        """Clean up resources on node destruction."""
        self.cap.release()
        cv2.destroyAllWindows()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = ColorCalibrator()
    try:
        node.run_calibration()
    except Exception as e:
        node.get_logger().error(f"Error during calibration: {e}")
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
