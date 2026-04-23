#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import Float32MultiArray
from cv_bridge import CvBridge
import cv2
import numpy as np

class ObjectDetector(Node):
    def __init__(self):
        super().__init__('object_detector')
        self.publisher_ = self.create_publisher(Float32MultiArray, '/object_coordinates', 10)
        self.subscription = self.create_subscription(Image, '/image_raw', self.image_callback, 10)
        self.bridge = CvBridge()
        self.lower_hsv = np.array([35, 100, 100]) # Default Green
        self.upper_hsv = np.array([85, 255, 255])

    def image_callback(self, data):
        frame = self.bridge.imgmsg_to_cv2(data, "bgr8")
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, self.lower_hsv, self.upper_hsv)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            c = max(contours, key=cv2.contourArea)
            ((x, y), radius) = cv2.minEnclosingCircle(c)
            if radius > 10:
                msg = Float32MultiArray()
                msg.data = [float(x), float(y), 0.0]
                self.publisher_.publish(msg)
        cv2.imshow("Detector", frame)
        cv2.waitKey(1)

def main(args=None):
    rclpy.init(args=args)
    node = ObjectDetector()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == "__main__":
    main()
