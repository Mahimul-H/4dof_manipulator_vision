# Quick Start Guide - 4-DOF Manipulator IK Control

## System Architecture
```
Camera → Vision Node → /pixel_coordinates → Controller Node (IK Solver)
         → /servo_angles → Serial Bridge → Arduino → Servos
```

---

## Docker Quick Commands

### Build and Run
```bash
# Build the Docker image
docker-compose build

# Start the container
docker-compose up -it manipulator-vision

# Stop the container
docker-compose down
```

### Inside Docker Container
```bash
# Source ROS 2 environment
source /opt/ros/humble/setup.bash
source /workspace/install/setup.bash

# Check available topics
ros2 topic list

# Monitor servo angles in real-time
ros2 topic echo /servo_angles

# Launch complete system
ros2 launch control_pkg manipulator_system_launch.py
```

---

## ROS 2 Parameters

### Default Configuration
| Parameter | Default | Description |
|-----------|---------|-------------|
| `link1_length` | 0.15 m | Shoulder-to-elbow arm segment |
| `link2_length` | 0.15 m | Elbow-to-wrist arm segment |
| `serial_port` | /dev/ttyUSB0 | Arduino connection |
| `baud_rate` | 115200 | Serial communication speed |
| `angle_min_safe` | 0° | Minimum servo angle limit |
| `angle_max_safe` | 180° | Maximum servo angle limit |

### Change Parameters at Launch
```bash
# Custom arm dimensions
ros2 launch control_pkg manipulator_system_launch.py \
  link1_length:=0.12 link2_length:=0.18

# Custom serial settings
ros2 launch control_pkg manipulator_system_launch.py \
  serial_port:=/dev/ttyACM0 baud_rate:=9600

# Restrict servo range
ros2 launch control_pkg manipulator_system_launch.py \
  angle_min_safe:=20.0 angle_max_safe:=160.0
```

### Change Parameters at Runtime
```bash
# Set parameter while node is running
ros2 param set /controller_node angle_min_safe 15.0

# Get current parameter value
ros2 param get /controller_node angle_max_safe

# List all node parameters
ros2 param list /controller_node
```

---

## Troubleshooting Serial Connection

### Check USB Device
```bash
# List all USB devices
lsusb

# List TTY devices
ls -la /dev/tty*

# Check if device is recognized
dmesg | tail -20
```

### Monitor Serial Port (Outside Docker)
```bash
# Use screen utility
screen /dev/ttyUSB0 115200

# Use minicom
minicom -D /dev/ttyUSB0 -b 115200

# Exit: Ctrl+A, then Q
```

### Test Serial Connection Inside Docker
```bash
# Check device exists in container
ls -la /dev/ttyUSB0

# Monitor incoming data
cat /dev/ttyUSB0

# Send test data
echo "90.0,45.0,120.0,90.0" > /dev/ttyUSB0
```

---

## Debugging IK Solver

### Enable Debug Output
```bash
# Launch with ROS 2 logging level set to DEBUG
ROS_LOG_LEVEL=DEBUG ros2 launch control_pkg manipulator_system_launch.py
```

### View Debug Messages
```bash
# In separate terminal, monitor controller node logs
ros2 node info /controller_node

# Check specific node communication
ros2 node list
ros2 node info /serial_bridge_node
```

### Test IK Manually
```bash
# Publish test pixel coordinates
ros2 topic pub /pixel_coordinates std_msgs/Float32MultiArray \
  "data: [320.0, 240.0, 50.0]"

# Monitor output
ros2 topic echo /servo_angles
```

---

## Common Issues & Solutions

### Issue: "Serial port permission denied"
```bash
# Solution: Add user to dialout group
sudo usermod -a -G dialout $USER
# Log out and log back in, then rebuild container
docker-compose build --no-cache
```

### Issue: "Node spins but no servo angles published"
```bash
# Check if pixel_coordinates are being published
ros2 topic echo /pixel_coordinates

# Verify IK solver is working
ros2 topic hz /servo_angles

# Check node logs
ros2 node info /controller_node
```

### Issue: "Arduino not receiving commands"
```bash
# Verify serial port in container
docker exec manipulator-vision-container ls -la /dev/ttyUSB0

# Check baud rate matches Arduino sketch
# Default: 115200

# Monitor serial communication
docker exec manipulator-vision-container cat /dev/ttyUSB0
```

### Issue: "IK returns unreachable target"
```bash
# Check arm workspace:
# Max reach = L1 + L2 + L4 = 0.1 + 0.15 + 0.15 + 0.05 = 0.45m

# Verify camera calibration:
# - Focal length should match camera specs (~500 for standard cameras)
# - Principal point should be near image center

# Use ROS 2 parameters to adjust:
ros2 launch control_pkg manipulator_system_launch.py \
  focal_length:=480.0 \
  center_x:=320.0 \
  center_y:=240.0
```

---

## File Locations

```
/home/cypher/Documents/4dof_manipulator_vision/
├── src/
│   ├── control_pkg/
│   │   ├── control_pkg/
│   │   │   ├── controller_node.py      ← Main IK solver
│   │   │   └── ik_solver.py
│   │   ├── launch/
│   │   │   ├── controller_launch.py    ← Launch file
│   │   │   └── manipulator_system_launch.py
│   │   └── setup.py
│   └── hardware_interface_pkg/
│       ├── hardware_interface_pkg/
│       │   └── serial_bridge.py        ← Serial interface
│       ├── launch/
│       │   └── serial_bridge_launch.py
│       └── setup.py
├── Dockerfile                           ← Docker config
├── docker-compose.yml                   ← Compose config
└── REFACTORING_SUMMARY.md              ← Full documentation
```

---

## Build & Deploy Workflow

### 1. Local Development
```bash
# Build packages locally
cd /workspace
source /opt/ros/humble/setup.bash
colcon build

# Test nodes
source install/setup.bash
ros2 launch control_pkg manipulator_system_launch.py
```

### 2. Docker Build
```bash
cd /home/cypher/Documents/4dof_manipulator_vision
docker-compose build
```

### 3. Docker Run
```bash
docker-compose up -it manipulator-vision
# Inside container:
source /workspace/install/setup.bash
ros2 launch control_pkg manipulator_system_launch.py serial_port:=/dev/ttyUSB0
```

### 4. Deployment Checklist
- [ ] Arduino firmware programmed with servo control code
- [ ] Serial cable connected to /dev/ttyUSB0
- [ ] Camera calibrated and vision node running
- [ ] Docker image built without errors
- [ ] Serial port visible in container
- [ ] ROS 2 parameters set correctly
- [ ] Test position reachable within arm workspace

---

## Expected Output

### Controller Node Starting
```
[controller_node-1] [INFO] [controller_node]: Controller node initialized - PC-side IK enabled
[controller_node-1] [INFO] [controller_node]: ========================================================================
[controller_node-1] [INFO] [controller_node]: [VISION INPUT - RAW PIXELS]
[controller_node-1] [INFO] [controller_node]:   X_pixel:   320.00px  |  Y_pixel:   240.00px  |  Radius:    50.00px
[controller_node-1] [INFO] [controller_node]: [3D WORLD COORDINATES - ROBOT BASE FRAME]
[controller_node-1] [INFO] [controller_node]:   X:    0.0000m  |  Y:    0.1000m  |  Z:    0.2500m
[controller_node-1] [INFO] [controller_node]: [JOINT ANGLES - DEGREES (AFTER SAFE ZONE CONSTRAINT)]
[controller_node-1] [INFO] [controller_node]:   θ1:    45.00°  |  θ2:    30.00°  |  θ3:    60.00°  |  θ4:    90.00°
[controller_node-1] [INFO] [controller_node]: [SERVO COMMAND - CSV FORMAT]
[controller_node-1] [INFO] [controller_node]:   45.0,30.0,60.0,90.0
```

### Serial Bridge Starting
```
[serial_bridge_node-1] [INFO] [serial_bridge_node]: Serial Bridge node initialized
[serial_bridge_node-1] [INFO] [serial_bridge_node]:   Serial Port: /dev/ttyUSB0
[serial_bridge_node-1] [INFO] [serial_bridge_node]:   Baud Rate: 115200
[serial_bridge_node-1] [INFO] [serial_bridge_node]:   Send Interval: 1.75s
[serial_bridge_node-1] [INFO] [serial_bridge_node]: Serial connection established: /dev/ttyUSB0 @ 115200 baud
[serial_bridge_node-1] [INFO] [serial_bridge_node]: Sent to Arduino [CSV]: 45.0,30.0,60.0,90.0
```

---

## Contact
For issues or questions, refer to `REFACTORING_SUMMARY.md` for detailed documentation.
