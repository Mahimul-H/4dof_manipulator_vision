import cv2
import numpy as np

def nothing(x):
    pass

def main():
    # Initialize webcam (0 is usually the integrated laptop cam)
    cap = cv2.VideoCapture(0)

    # Create a window for trackbars
    cv2.namedWindow("Trackbars")
    cv2.createTrackbar("L-H", "Trackbars", 0, 179, nothing)
    cv2.createTrackbar("L-S", "Trackbars", 0, 255, nothing)
    cv2.createTrackbar("L-V", "Trackbars", 0, 255, nothing)
    cv2.createTrackbar("U-H", "Trackbars", 179, 179, nothing)
    cv2.createTrackbar("U-S", "Trackbars", 255, 255, nothing)
    cv2.createTrackbar("U-V", "Trackbars", 255, 255, nothing)

    print("Adjust sliders until your object is WHITE and background is BLACK.")
    print("Press 'q' to exit and save values.")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # Get current positions of trackbars
        l_h = cv2.getTrackbarPos("L-H", "Trackbars")
        l_s = cv2.getTrackbarPos("L-S", "Trackbars")
        l_v = cv2.getTrackbarPos("L-V", "Trackbars")
        u_h = cv2.getTrackbarPos("U-H", "Trackbars")
        u_s = cv2.getTrackbarPos("U-S", "Trackbars")
        u_v = cv2.getTrackbarPos("U-V", "Trackbars")

        lower_range = np.array([l_h, l_s, l_v])
        upper_range = np.array([u_h, u_s, u_v])

        mask = cv2.inRange(hsv, lower_range, upper_range)
        result = cv2.bitwise_and(frame, frame, mask=mask)

        cv2.imshow("Frame", frame)
        cv2.imshow("Mask", mask)
        cv2.imshow("Filtered Result", result)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            print(f"Final HSV Range: Lower[{l_h}, {l_s}, {l_v}], Upper[{u_h}, {u_s}, {u_v}]")
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    main()