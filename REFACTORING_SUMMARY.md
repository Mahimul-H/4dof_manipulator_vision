# ROS 2 4-DOF Manipulator IK Control Loop Refactoring

## Overview
This document summarizes the comprehensive refactoring of the ROS 2 project to implement a PC-side Inverse Kinematics (IK) control loop with Docker deployment support.

---

## 1. Control Node Refactoring (`control_pkg/control_node.py`)

### Changes Made:
- **Replaced world coordinate publishing** with direct servo angle publishing
- **Topic change**: `/object_coordinates` → `/servo_angles`
- **Message type**: Float32MultiArray with 4 values: [Base, Shoulder, Elbow, Wrist] angles in **degrees**

### Key Features:
- **PC-side IK Solver**: Converts pixel coordinates → 3D world coordinates → 4 servo angles
- **Link Lengths**: L1=0.15m (shoulder-elbow), L2=0.15m (elbow-wrist)
- **IK Algorithm**: Law of Cosines for 3-DOF vertical plane + base rotation
- **Safe Zone Constraints**: Angles clamped to [0°, 180°] (configurable via ROS parameters)

### New ROS Parameters:
```yaml
link1_length: 0.15           # Shoulder-to-elbow link length (meters)
link2_length: 0.15           # Elbow-to-wrist link length (meters)
focal_length: 500.0          # Camera focal length (pixels)
center_x: 320.0              # Principal point X (pixels)
center_y: 240.0              # Principal point Y (pixels)
table_height: 0.25           # Table height / Z coordinate (meters)
base_offset_y: 0.10          # Camera offset from robot base (meters)
angle_min_safe: 0.0          # Minimum safe angle (degrees)
angle_max_safe: 180.0        # Maximum safe angle (degrees)
```

### Constraint Logic:
```python
def _constrain_angle(self, angle_deg):
    """Apply safe zone constraints"""
    return max(self.angle_min_safe, min(self.angle_max_safe, angle_deg))
```

### Example Output:
```
[SERVO COMMAND - CSV FORMAT]
  90.0,45.0,120.0,90.0
```

---

## 2. Serial Bridge Refactoring (`hardware_interface_pkg/serial_bridge_node.py`)

### Changes Made:
- **Subscription update**: `/object_coordinates` → `/servo_angles`
- **Message format**: Now accepts 4 servo angles instead of 3 world coordinates
- **Serial protocol**: CSV format `"angle1,angle2,angle3,angle4\n"`
- **Enhanced error handling**: Graceful handling of SerialException with reconnection logic

### New Features:
- **Automatic Reconnection**: If USB is unplugged, node stays alive and attempts reconnection
- **Rate Limiting**: Configurable send interval (default: 1.75 seconds)
- **Robust Error Handling**: Non-fatal serial errors logged but don't crash the node

### New ROS Parameters:
```yaml
serial_port: '/dev/ttyUSB0'  # Serial port path
baud_rate: 115200            # Baud rate
send_interval: 1.75          # Min interval between sends (seconds)
```

### Error Handling Flow:
```
Try Write → SerialException → Log Error → Mark Serial as None
→ Next Message Triggers Reconnection Attempt → Resume Sending
```

### Example Serial Output:
```
90.0,45.0,120.0,90.0
```

---

## 3. Dockerization

### Dockerfile Updates (`Dockerfile`)
**New dependencies installed:**
- `python3-serial`: PySerial library for serial communication
- `libopencv-dev`: OpenCV development headers
- Comments and organization improved

**Docker Build Steps:**
1. Base image: `ros:humble-ros-base`
2. Install system dependencies (build-essential, python3-pip, etc.)
3. Copy workspace and install ROS 2 dependencies via rosdep
4. Build packages with `colcon build`
5. Set up entrypoint

### docker-compose.yml Updates
**New configurations:**
```yaml
devices:
  - /dev/ttyUSB0:/dev/ttyUSB0    # Serial device mapping for Arduino

privileged: true                  # Required for serial access

container_name: manipulator-vision-container  # Named container
```

**Preserved configurations:**
- X11 display sharing for OpenCV windows
- `network_mode: host` for ROS 2 communication
- Volume mounts for code development

---

## 4. Launch Files

### Controller Node Launch (`control_pkg/launch/controller_launch.py`)
**Features:**
- Configurable arm parameters (link lengths)
- Configurable camera parameters (focal length, principal point)
- Configurable safety constraints (angle min/max)
- Clean output to console

**Usage:**
```bash
ros2 launch control_pkg controller_launch.py \
  link1_length:=0.15 \
  link2_length:=0.15 \
  angle_min_safe:=0.0 \
  angle_max_safe:=180.0
```

### Serial Bridge Launch (`hardware_interface_pkg/launch/serial_bridge_launch.py`)
**Features:**
- Configurable serial port
- Configurable baud rate
- Configurable send interval

**Usage:**
```bash
ros2 launch hardware_interface_pkg serial_bridge_launch.py \
  serial_port:=/dev/ttyUSB0 \
  baud_rate:=115200
```

### System Launch (`control_pkg/launch/manipulator_system_launch.py`)
**Features:**
- Launches both controller and serial bridge in one command
- Single parameter interface for coordinated operation
- Recommended for production use

**Usage:**
```bash
ros2 launch control_pkg manipulator_system_launch.py \
  link1_length:=0.15 \
  link2_length:=0.15 \
  serial_port:=/dev/ttyUSB0 \
  angle_min_safe:=0.0 \
  angle_max_safe:=180.0
```

---

## 5. Dependencies

### control_pkg/setup.py
```python
install_requires=['setuptools', 'rclpy', 'numpy']
```
- Added: Launch file data packaging

### hardware_interface_pkg/setup.py
```python
install_requires=['setuptools', 'rclpy', 'pyserial']
```
- Added: rclpy (was missing), launch file data packaging

---

## ROS 2 Topic/Message Flow

### Before Refactoring:
```
Vision Node
    ↓
[/pixel_coordinates]
    ↓
Controller Node (computes IK)
    ↓
[/object_coordinates] (3D world coords)
    ↓
Serial Bridge Node
    ↓
Arduino (receives world coords, no servo angles)
```

### After Refactoring:
```
Vision Node
    ↓
[/pixel_coordinates]
    ↓
Controller Node (computes IK on PC)
    ↓
[/servo_angles] (4 servo angles in degrees)
    ↓
Serial Bridge Node
    ↓
Arduino (receives servo angles, directly controls servos)
```

---

## Docker Deployment

### Build Image:
```bash
docker-compose build
```

### Run Container:
```bash
docker-compose up -it manipulator-vision
```

### Inside Container:
```bash
# Source ROS 2 setup
source /opt/ros/humble/setup.bash
source /workspace/install/setup.bash

# Launch the complete system
ros2 launch control_pkg manipulator_system_launch.py \
  serial_port:=/dev/ttyUSB0 \
  baud_rate:=115200
```

---

## Configuration via Launch Parameters

### Change Serial Port:
```bash
ros2 launch control_pkg manipulator_system_launch.py \
  serial_port:=/dev/ttyACM0
```

### Change Safe Zone (Angles):
```bash
ros2 launch control_pkg manipulator_system_launch.py \
  angle_min_safe:=10.0 \
  angle_max_safe:=170.0
```

### Change Arm Link Lengths:
```bash
ros2 launch control_pkg manipulator_system_launch.py \
  link1_length:=0.12 \
  link2_length:=0.18
```

---

## Testing Checklist

### Before Deployment:
- [ ] Verify Docker build completes without errors
- [ ] Verify serial device is mounted at `/dev/ttyUSB0`
- [ ] Verify camera feed is available
- [ ] Test IK solver with known positions
- [ ] Test safe zone constraints with boundary angles

### System Integration:
- [ ] Vision node publishes `/pixel_coordinates`
- [ ] Controller node subscribes to `/pixel_coordinates` and publishes `/servo_angles`
- [ ] Serial bridge subscribes to `/servo_angles` and sends via serial
- [ ] Arduino receives servo commands in CSV format
- [ ] Servos move to commanded angles

### Error Scenarios:
- [ ] Unplug USB cable mid-operation → verify node stays alive and reconnects
- [ ] Invalid target position → verify unreachable message and no crash
- [ ] Serial timeout → verify graceful error handling
- [ ] Change ROS parameter → verify node updates without restart

---

## File Changes Summary

| File | Change | Type |
|------|--------|------|
| `control_pkg/control_node.py` | PC-side IK with angle publishing | Core Logic |
| `hardware_interface_pkg/serial_bridge.py` | Servo angle listener + error handling | Core Logic |
| `Dockerfile` | Added python3-serial, libopencv-dev | Infrastructure |
| `docker-compose.yml` | Added /dev/ttyUSB0, privileged mode | Infrastructure |
| `control_pkg/setup.py` | Added launch files, updated description | Config |
| `hardware_interface_pkg/setup.py` | Added launch files, added rclpy | Config |
| `control_pkg/launch/controller_launch.py` | NEW: Parametrized controller | Launch |
| `hardware_interface_pkg/launch/serial_bridge_launch.py` | NEW: Parametrized serial bridge | Launch |
| `control_pkg/launch/manipulator_system_launch.py` | NEW: Complete system launch | Launch |

---

## Architecture Benefits

### 1. **Modularity**
- Controller and serial bridge are independent ROS nodes
- Easy to replace or extend individual components

### 2. **Parameter-Driven Configuration**
- No hardcoding of serial ports, link lengths, or safety constraints
- Change parameters via launch files or `ros2 param set`

### 3. **Robustness**
- Graceful handling of serial port disconnections
- Node stays alive even if USB is unplugged
- Automatic reconnection on next message

### 4. **Docker Deployment**
- Reproducible builds across machines
- Pre-configured dependencies and ROS 2 environment
- Easy testing on CI/CD systems

### 5. **Debugging**
- Detailed logging at each transformation step
- Log messages show: pixels → 3D coords → raw angles → constrained angles → CSV command
- Easy to identify bottlenecks or issues

---

## Future Enhancements

1. **Dynamic Reconfiguration**: Use `dynamic_reconfigure` for runtime parameter updates without node restart
2. **Trajectory Planning**: Add trajectory generation between waypoints
3. **Collision Avoidance**: Integrate with MoveIt2 for advanced planning
4. **Monitoring Dashboard**: RViz visualization of arm configuration and reachability
5. **Logging & Telemetry**: Record all servo commands for post-analysis
6. **Multi-Robot Support**: Extend to support multiple manipulators on same PC

---

## Troubleshooting

### "Serial port not found"
- Verify USB cable is connected
- Check device: `ls -la /dev/ttyUSB*`
- Update parameter: `serial_port:=/dev/ttyACM0` (if using Arduino Uno)

### "Target unreachable"
- Verify arm link lengths match your hardware
- Check if target position is within workspace
- Increase `angle_max_safe` if servos can rotate beyond 180°

### "Node crashes on IK computation"
- Verify camera intrinsics (focal length, principal point)
- Check table height matches actual setup
- Look for non-finite numbers in debug logs

### "Arduino not receiving commands"
- Verify baud rate matches Arduino sketch: `baud_rate:=115200`
- Check CSV format: should be `"90.0,45.0,120.0,90.0\n"`
- Monitor serial port: `cat /dev/ttyUSB0` or use `screen /dev/ttyUSB0 115200`

---

## Contact & Support
Maintained by: Robotics Team
Created: 2026-04-25
License: Apache 2.0
