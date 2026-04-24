"""Inverse Kinematics solver for 4-DOF robotic arm."""
import math


class IKSolver4DOF:
    """Inverse kinematics solver for 4-DOF arm with configuration:
    - Base rotation (theta1): horizontal rotation around Z-axis
    - Shoulder (theta2), Elbow (theta3), Wrist (theta4): vertical plane joints

    Link lengths: L1 (base/offset), L2 (shoulder-elbow), L3 (elbow-wrist), L4 (wrist-tool)
    """

    def __init__(self, L1=0.1, L2=0.15, L3=0.15, L4=0.05):
        """Initialize arm link lengths.

        Args:
            L1: Base height or shoulder offset (meters)
            L2: Shoulder to elbow link length (meters)
            L3: Elbow to wrist link length (meters)
            L4: Wrist to end-effector link length (meters)
        """
        self.L1 = L1
        self.L2 = L2
        self.L3 = L3
        self.L4 = L4

    def solve(self, target_x, target_y, target_z, logger=None):
        """Compute inverse kinematics for target position.

        Args:
            target_x: Target X coordinate (meters)
            target_y: Target Y coordinate (meters)
            target_z: Target Z coordinate (meters)
            logger: Optional ROS 2 logger for debug output

        Returns:
            List of 4 joint angles [theta1, theta2, theta3, theta4] in radians,
            or None if target is unreachable.
        """
        # Step 1: Base rotation (theta1)
        theta1 = math.atan2(target_y, target_x)
        if logger:
            logger.debug(
                f"[IK Step 1] Base rotation (θ1): {math.degrees(theta1):.2f}° "
                f"from atan2({target_y:.4f}, {target_x:.4f})")

        # Step 2: Project to vertical plane
        horizontal_distance = math.sqrt(target_x**2 + target_y**2)
        if logger:
            logger.debug(
                f"[IK Step 2] Horizontal distance: {horizontal_distance:.4f}m")

        # Step 3: Solve 3-DOF IK in vertical plane (L2, L3, L4)
        shoulder_height = self.L1
        target_height = target_z - shoulder_height
        target_distance = math.sqrt(
            horizontal_distance**2 + target_height**2)

        if logger:
            logger.debug(
                f"[IK Step 3] Shoulder height (L1): {shoulder_height:.4f}m, "
                f"Target height above shoulder: {target_height:.4f}m")
            logger.debug(
                f"[IK Step 3] Distance from shoulder to target: "
                f"{target_distance:.4f}m")

        # Check reachability
        max_reach = self.L2 + self.L3 + self.L4
        if logger:
            logger.debug(
                f"[IK Reachability] Max reach: {max_reach:.4f}m, "
                f"Target distance: {target_distance:.4f}m, "
                f"Reachable: {target_distance <= max_reach}")

        if target_distance > max_reach:
            if logger:
                logger.warn(
                    f"Target unreachable: distance {target_distance:.4f}m "
                    f"> max_reach {max_reach:.4f}m")
            return None

        # Step 4: Law of cosines for 3-link arm
        try:
            gamma = math.atan2(target_height, horizontal_distance)
            if logger:
                logger.debug(
                    f"[IK Step 4] Angle to target (γ): {math.degrees(gamma):.2f}°")

            combined_length = self.L3 + self.L4
            cos_theta3 = (self.L2**2 + combined_length**2 - target_distance**2) / \
                (2 * self.L2 * combined_length)

            if logger:
                logger.debug(
                    f"[IK Step 4] Law of cosines: "
                    f"cos(θ3) = {cos_theta3:.6f}")

            if abs(cos_theta3) > 1.0:
                if logger:
                    logger.warn(
                        f"IK computation failed: cos(θ3)={cos_theta3:.6f} "
                        f"out of valid range [-1, 1]")
                return None

            theta3 = math.acos(cos_theta3)
            if logger:
                logger.debug(
                    f"[IK Step 4] Elbow angle (θ3): {math.degrees(theta3):.2f}°")

            # Angle of L3+L4 segment
            delta = math.atan2(self.L3 * math.sin(theta3),
                              self.L2 + self.L3 * math.cos(theta3))

            theta2 = gamma - delta
            theta4 = -theta2 - theta3

            if logger:
                logger.debug(
                    f"[IK Step 4] Shoulder angle (θ2): {math.degrees(theta2):.2f}°, "
                    f"Wrist angle (θ4): {math.degrees(theta4):.2f}°")

            return [theta1, theta2, theta3, theta4]

        except (ValueError, ZeroDivisionError) as e:
            if logger:
                logger.error(
                    f"IK computation error: {type(e).__name__}: {e}")
            return None

    def format_arduino_command(self, angles):
        """Format joint angles into Arduino-compatible string.

        Args:
            angles: List of 4 angles in radians

        Returns:
            String formatted as "theta1,theta2,theta3,theta4\n"
        """
        if angles is None:
            return None
        theta1, theta2, theta3, theta4 = angles
        return f"{theta1:.6f},{theta2:.6f},{theta3:.6f},{theta4:.6f}\n"
