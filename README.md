# 4-DOF Manipulator Vision System

A ROS 2 Humble-based project for vision-guided inverse kinematics control of a 4-DOF robotic manipulator arm. The system features PC-side IK computation, real-time servo angle calculation, and robust serial communication with Arduino-based motor control.

## Table of Contents

- [Overview](#overview)
- [System Architecture](#system-architecture)
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Configuration](#configuration)
- [Project Structure](#project-structure)
- [Nodes and Topics](#nodes-and-topics)
- [Usage Examples](#usage-examples)
- [Docker Deployment](#docker-deployment)
- [Troubleshooting](#troubleshooting)
- [References](#references)

---

## Overview

This project integrates computer vision, inverse kinematics, and hardware control to create an autonomous 4-DOF robotic arm system. The vision system detects target objects in real-time, the control system computes required servo angles using IK algorithms, and the hardware interface sends commands to Arduino-controlled servo motors.

### Key Specifications

- **Arm Configuration**: 4 degrees of freedom (Base rotation, Shoulder, Elbow, Wrist)
- **Link Lengths**: L1=0.15m (shoulder-elbow), L2=0.15m (elbow-wrist)
- **Base Height**: L0=0.1m, Wrist-to-tool: 0.05m
- **Servo Range**: 0-180 degrees per servo
- **Max Reach**: ~0.45 meters
- **Control Rate**: 1.75 seconds between command sends (configurable)

---

## System Architecture

### Data Flow

```
Video Stream
     |
     v
Vision Node (vision_pkg)
[Detects objects in camera feed]
     |
     v
/pixel_coordinates [px_x, px_y, radius]
     |
     v
Controller Node (control_pkg)
[Converts pixels to 3D world coords]
[Computes IK using Law of Cosines]
[Applies servo constraints 0-180]
     |
     v
/servo_angles [theta1, theta2, theta3, theta4] in degrees
     |
     v
Serial Bridge Node (hardware_interface_pkg)
[Rounds to integers]
[Formats CSV: "90,45,120,90"]
[Sends via serial to Arduino]
     |
     v
Arduino Firmware
[Receives servo commands]
[Controls servo motors]
     |
     v
Physical Manipulator Arm
```

### Component Interaction

```
control_pkg:
  - controller_node.py    [Main IK solver]
  - ik_solver.py          [IK algorithm implementation]
  - launch/               [Launch configurations]

hardware_interface_pkg:
  - serial_bridge.py      [Serial communication]
  - launch/               [Launch configurations]

vision_pkg:
  - detector.py           [Object detection]
  - calibrator.py         [Camera calibration]

Docker:
  - Dockerfile            [Container definition]
  - docker-compose.yml    [Compose configuration]
```

---

## Features

### PC-Side Inverse Kinematics

- Computes servo angles on the main computer for complex calculations
- Supports Law of Cosines algorithm for 4-DOF arm
- Real-time angle computation with minimal latency

### Vision Integration

- Camera calibration tools (focal length, principal point)
- Object detection and tracking
- Pixel-to-3D world coordinate transformation
- Configurable camera intrinsics via ROS parameters

### Robust Hardware Interface

- Auto-reconnection on serial port disconnect
- Graceful error handling (node stays alive during cable issues)
- Rate limiting to prevent serial buffer overflow
- Comprehensive logging and debugging output

### Parameter-Driven Configuration

- All system parameters configurable via launch files
- No code changes required for different hardware setups
- Runtime parameter adjustment via ROS 2 parameter service

### Docker Deployment

- Reproducible builds across machines
- Pre-configured dependencies and ROS 2 environment
- X11 display sharing for OpenCV visualization
- USB device mapping for camera and Arduino serial connection
- Docker Compose for simplified management

---

## Prerequisites

### Hardware

- 4-DOF robotic arm with servo motors (0-180 degree range)
- Arduino microcontroller (Uno, Mega, or compatible)
- USB camera (minimum 640x480 resolution recommended)
- USB serial cable for Arduino connection
- Computer with Linux (Ubuntu 22.04+ recommended)

### Software

- Docker and Docker Compose (for containerized deployment)
- ROS 2 Humble (or use Docker to avoid installation)
- Python 3.10+
- OpenCV (python3-opencv)
- PySerial (python3-serial)

### System Libraries

```bash
sudo apt-get install -y \
    python3-colcon-common-extensions \
    python3-pip \
    python3-opencv \
    python3-numpy \
    python3-rosdep \
    python3-serial \
    libopencv-dev
```

---

## Quick Start

### Using Docker Compose (Recommended)

```bash
# Navigate to project directory
cd /home/cypher/Documents/4dof_manipulator_vision

# Build and start container
docker-compose up --build

# Inside container: Start the complete system
ros2 launch control_pkg manipulator_system_launch.py
```

### Using Docker Directly

```bash
# Build image
docker build -t manipulator-vision:latest .

# Start container
docker run --rm -it \
  -v "$(pwd)":/workspace \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  -e DISPLAY=$DISPLAY \
  --device /dev/video0 \
  --device /dev/ttyUSB0 \
  --network host \
  manipulator-vision:latest

# Inside container
source /opt/ros/humble/setup.bash
source /workspace/install/setup.bash
ros2 launch control_pkg manipulator_system_launch.py
```

### Local Installation

```bash
# Install ROS 2 Humble (refer to official documentation)
# Then install dependencies
sudo apt-get install python3-colcon-common-extensions python3-pip python3-rosdep

# Clone or navigate to project
cd /path/to/4dof_manipulator_vision

# Build packages
colcon build

# Source setup script
source install/setup.bash

# Launch system
ros2 launch control_pkg manipulator_system_launch.py
```

---

## Installation

### Step 1: Clone Repository

```bash
cd ~/Documents
git clone <repository-url> 4dof_manipulator_vision
cd 4dof_manipulator_vision
```

### Step 2: Install Dependencies (Non-Docker)

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install ROS 2 Humble (if not already installed)
# Follow: https://docs.ros.org/en/humble/Installation.html

# Install required Python packages
sudo apt-get install -y python3-pip python3-serial python3-numpy

# Install OpenCV and development tools
sudo apt-get install -y python3-opencv libopencv-dev
```

### Step 3: Build ROS 2 Packages

```bash
cd ~/Documents/4dof_manipulator_vision

# Verify build configuration
rosdep init  # May fail if already initialized
rosdep update

# Install package dependencies
rosdep install --from-paths src --ignore-src -r -y

# Build all packages
colcon build

# Build specific package (if needed)
colcon build --packages-select control_pkg
colcon build --packages-select hardware_interface_pkg
```

### Step 4: Source Setup

```bash
# Source ROS 2 installation
source /opt/ros/humble/setup.bash

# Source workspace installation
source ~/Documents/4dof_manipulator_vision/install/setup.bash

# Add to .bashrc for convenience
echo "source ~/Documents/4dof_manipulator_vision/install/setup.bash" >> ~/.bashrc
```

### Step 5: Verify Installation

```bash
# Check if nodes are accessible
ros2 pkg list | grep control_pkg
ros2 pkg list | grep hardware_interface_pkg

# View available launch files
ros2 launch control_pkg controller_launch.py --show-args
ros2 launch hardware_interface_pkg serial_bridge_launch.py --show-args
```

---

## Configuration

### ROS 2 Parameters

#### Controller Node Parameters

Configure via launch file or command line:

```yaml
link1_length: 0.15              # Shoulder-elbow segment length (meters)
link2_length: 0.15              # Elbow-wrist segment length (meters)
focal_length: 500.0             # Camera focal length (pixels)
center_x: 320.0                 # Principal point X (pixels)
center_y: 240.0                 # Principal point Y (pixels)
table_height: 0.25              # Table/workspace height (meters)
base_offset_y: 0.10             # Camera offset from base (meters)
angle_min_safe: 0.0             # Minimum servo angle (degrees)
angle_max_safe: 180.0           # Maximum servo angle (degrees)
```

#### Serial Bridge Parameters

```yaml
serial_port: '/dev/ttyUSB0'     # Arduino serial device
baud_rate: 115200               # Serial communication speed
send_interval: 1.75             # Min time between commands (seconds)
```

### Customizing Parameters

#### Via Launch File

```bash
ros2 launch control_pkg manipulator_system_launch.py \
  link1_length:=0.12 \
  link2_length:=0.18 \
  serial_port:=/dev/ttyACM0 \
  baud_rate:=9600
```

#### At Runtime

```bash
# Set parameter while node is running
ros2 param set /controller_node angle_max_safe 170.0

# Get current value
ros2 param get /controller_node angle_max_safe

# List all parameters
ros2 param list /controller_node
```

#### Via Configuration File

Create `config.yaml`:

```yaml
controller_node:
  ros__parameters:
    link1_length: 0.15
    link2_length: 0.15
    angle_min_safe: 0.0
    angle_max_safe: 180.0

serial_bridge_node:
  ros__parameters:
    serial_port: '/dev/ttyUSB0'
    baud_rate: 115200
```

Launch with config:

```bash
ros2 launch control_pkg controller_launch.py --params-file config.yaml
```

---

## Project Structure

```
4dof_manipulator_vision/
├── src/
│   ├── control_pkg/
│   │   ├── control_pkg/
│   │   │   ├── __init__.py
│   │   │   ├── controller_node.py       Main IK solver and servo publisher
│   │   │   └── ik_solver.py             IK algorithm implementation
│   │   ├── launch/
│   │   │   ├── controller_launch.py     Controller launch configuration
│   │   │   └── manipulator_system_launch.py  Complete system launcher
│   │   ├── package.xml
│   │   ├── setup.py
│   │   ├── setup.cfg
│   │   └── test/
│   │
│   ├── hardware_interface_pkg/
│   │   ├── hardware_interface_pkg/
│   │   │   ├── __init__.py
│   │   │   └── serial_bridge.py        Serial communication with Arduino
│   │   ├── launch/
│   │   │   └── serial_bridge_launch.py Serial bridge launch configuration
│   │   ├── package.xml
│   │   ├── setup.py
│   │   ├── setup.cfg
│   │   └── test/
│   │
│   └── vision_pkg/
│       ├── vision_pkg/
│       │   ├── detector.py             Object detection node
│       │   └── calibrator.py           Camera calibration node
│       ├── package.xml
│       ├── setup.py
│       └── test/
│
├── build/                               Colcon build output
├── install/                             Colcon install output
├── log/                                 ROS 2 build logs
│
├── Dockerfile                           Docker container definition
├── docker-compose.yml                   Docker Compose configuration
├── ros_entrypoint.sh                    ROS 2 entrypoint script
│
├── README.md                            This file
├── REFACTORING_SUMMARY.md              Detailed technical documentation
├── QUICK_START.md                      Developer quick reference
├── BEFORE_AFTER_COMPARISON.md          Architecture comparison
└── LICENSE
```

---

## Nodes and Topics

### Controller Node

**Executable**: control_pkg.controller_node

**Subscribes to**:
- `/pixel_coordinates` [Float32MultiArray] - Pixel coordinates from vision system

**Publishes**:
- `/servo_angles` [Float32MultiArray] - 4 servo angles in degrees [0-180]

**Key Functions**:
- Converts pixel coordinates to 3D world coordinates
- Computes inverse kinematics using Law of Cosines
- Applies safety constraints (0-180 degree range)
- Adds servo offsets (90 degrees for shoulder and elbow)

**Log Output Example**:
```
[INFO] [VISION INPUT - RAW PIXELS]
[INFO]   X_pixel: 320.00px | Y_pixel: 240.00px | Radius: 50.00px
[INFO] [3D WORLD COORDINATES - ROBOT BASE FRAME]
[INFO]   X: 0.0000m | Y: 0.1000m | Z: 0.2500m
[INFO] [ARDUINO COMMAND - INTEGER DEGREES (0-180)]
[INFO]   90, 60, 150, 90
```

### Serial Bridge Node

**Executable**: hardware_interface_pkg.serial_bridge

**Subscribes to**:
- `/servo_angles` [Float32MultiArray] - Servo angles from controller

**Publishes**:
- None (writes directly to serial port)

**Key Functions**:
- Receives servo angles from controller
- Rounds floats to integers
- Formats as CSV string: "90,60,150,90\n"
- Sends to Arduino via serial port
- Auto-reconnects on disconnection
- Handles serial errors gracefully

**Log Output Example**:
```
[INFO] Serial Bridge node initialized
[INFO]   Serial Port: /dev/ttyUSB0
[INFO]   Baud Rate: 115200
[INFO] Serial connection established: /dev/ttyUSB0 @ 115200 baud
[INFO] Sending to Arduino: '90,60,150,90'
[INFO] Successfully sent: 90,60,150,90
```

### Vision Nodes (vision_pkg)

**Detector Node**: object_detection, publishes `/pixel_coordinates`

**Calibrator Node**: camera calibration tool

---

## Usage Examples

### Example 1: Complete System with Default Parameters

```bash
# Terminal 1: Build and source
cd ~/Documents/4dof_manipulator_vision
colcon build
source install/setup.bash

# Terminal 2: Launch complete system
ros2 launch control_pkg manipulator_system_launch.py

# Terminal 3: Monitor output
ros2 topic echo /servo_angles
```

### Example 2: Custom Arm Configuration

```bash
# For a different robot with 12cm and 18cm links
ros2 launch control_pkg manipulator_system_launch.py \
  link1_length:=0.12 \
  link2_length:=0.18
```

### Example 3: Custom Serial Port

```bash
# For Arduino connected to /dev/ttyACM0
ros2 launch control_pkg manipulator_system_launch.py \
  serial_port:=/dev/ttyACM0 \
  baud_rate:=9600
```

### Example 4: Restricted Servo Range

```bash
# Limit servos to 20-160 degrees for safety
ros2 launch control_pkg manipulator_system_launch.py \
  angle_min_safe:=20.0 \
  angle_max_safe:=160.0
```

### Example 5: Testing Without Vision

Manually publish servo angles to test serial communication:

```bash
# Terminal 1: Start serial bridge only
ros2 launch hardware_interface_pkg serial_bridge_launch.py

# Terminal 2: Send test command
ros2 topic pub --once /servo_angles std_msgs/msg/Float32MultiArray \
  "{data: [90.0, 45.0, 120.0, 90.0]}"

# Monitor serial output (outside ROS)
cat /dev/ttyUSB0
# Output: 90,45,120,90
```

### Example 6: Industrial Robot Workspace Test

Test arm reaching different workspace positions:

```bash
# Terminal 1: Launch system
ros2 launch control_pkg manipulator_system_launch.py

# Terminal 2: Home position
ros2 topic pub --once /pixel_coordinates std_msgs/msg/Float32MultiArray \
  "{data: [320.0, 240.0, 50.0]}"

# Center of image should correspond to arm home position
```

---

## Docker Deployment

### Building Docker Image

```bash
cd ~/Documents/4dof_manipulator_vision

# Build with docker-compose
docker-compose build

# Or build directly
docker build -t manipulator-vision:latest .
```

### Running with Docker Compose

```bash
# Start container with interactive shell
docker-compose up -it

# Inside container
source /workspace/install/setup.bash
ros2 launch control_pkg manipulator_system_launch.py

# In another docker terminal
docker-compose exec manipulator-vision bash
ros2 topic echo /servo_angles
```

### Running with Docker CLI

```bash
# Run container
docker run --rm -it \
  --volume "$(pwd)":/workspace:rw \
  --volume /tmp/.X11-unix:/tmp/.X11-unix \
  --device /dev/video0:/dev/video0 \
  --device /dev/ttyUSB0:/dev/ttyUSB0 \
  --env DISPLAY=$DISPLAY \
  --network host \
  --privileged \
  manipulator-vision:latest

# Inside container
source /workspace/install/setup.bash
ros2 launch control_pkg manipulator_system_launch.py
```

### Dockerfile Features

- Base image: ros:humble-ros-base
- Pre-installed: python3-serial, python3-opencv, libopencv-dev
- Pre-configured: ROS 2 environment, workspace setup
- Supports: USB device mapping, X11 forwarding, network host mode

### Docker Compose Features

- Automatic build on startup
- Volume mounting for live code editing
- X11 display sharing for GUI applications
- USB device mapping for camera and Arduino
- Network mode: host for ROS 2 communication
- Privileged mode for serial port access

---

## Troubleshooting

### Issue: "Serial port not found" or "Permission denied"

**Causes**:
- USB cable not connected
- Wrong device path (/dev/ttyUSB0 vs /dev/ttyACM0)
- Insufficient permissions

**Solutions**:

```bash
# Check connected devices
ls -la /dev/tty*
lsusb

# Add user to dialout group (requires logout/login)
sudo usermod -a -G dialout $USER

# Change permissions (temporary)
sudo chmod 666 /dev/ttyUSB0

# Specify correct port
ros2 launch control_pkg manipulator_system_launch.py serial_port:=/dev/ttyACM0
```

### Issue: "Node spins but no servo angles published"

**Causes**:
- Vision node not running (no pixel coordinates)
- IK solver marking target as unreachable
- Controller node crashed

**Solutions**:

```bash
# Check if vision node is running
ros2 node list

# Monitor controller node output
ros2 node info /controller_node

# Test manually
ros2 topic pub --once /pixel_coordinates std_msgs/msg/Float32MultiArray \
  "{data: [320.0, 240.0, 50.0]}"

# Monitor servo angles
ros2 topic echo /servo_angles
```

### Issue: "Target unreachable"

**Causes**:
- Target position outside arm workspace
- Incorrect camera calibration
- Arm link lengths don't match configuration

**Solutions**:

```bash
# Verify camera parameters
ros2 param get /controller_node focal_length
ros2 param get /controller_node center_x

# Check arm reach
# Max reach = 0.1 + 0.15 + 0.15 + 0.05 = 0.45m

# Adjust link lengths
ros2 launch control_pkg manipulator_system_launch.py \
  link1_length:=0.15 \
  link2_length:=0.15
```

### Issue: Arduino not receiving commands

**Causes**:
- Serial port not mapped in Docker
- Baud rate mismatch
- Serial buffer full (too many commands)

**Solutions**:

```bash
# Docker: Verify device mapping
docker inspect manipulator-vision | grep device

# Test serial connection
cat /dev/ttyUSB0  # Monitor data
echo "90,45,120,90" > /dev/ttyUSB0  # Send test

# Increase send interval
ros2 launch control_pkg manipulator_system_launch.py send_interval:=2.5
```

### Issue: USB disconnects during operation

**Expected Behavior**: Node stays alive and auto-reconnects

**Verification**:

```bash
# Monitor logs
ros2 topic echo /servo_angles

# Unplug cable - should see error messages
# Plug back in - node should auto-reconnect
```

### Issue: Docker build fails

**Solutions**:

```bash
# Clear Docker cache
docker system prune

# Rebuild with no cache
docker-compose build --no-cache

# Check internet connection and disk space
df -h
```

---

## References

### Documentation Files

- [REFACTORING_SUMMARY.md](REFACTORING_SUMMARY.md) - Complete technical reference
- [QUICK_START.md](QUICK_START.md) - Developer quick reference guide
- [BEFORE_AFTER_COMPARISON.md](BEFORE_AFTER_COMPARISON.md) - Architecture changes

### External Resources

- ROS 2 Humble Documentation: https://docs.ros.org/en/humble/
- ROS 2 Launch Documentation: https://docs.ros.org/en/humble/Concepts/Intermediate/Launch/Basic-Launch-File-Example.html
- OpenCV Documentation: https://docs.opencv.org/
- Arduino Serial Communication: https://docs.arduino.cc/built-in-examples/communication/SerialComm/

### IK Algorithm

The controller uses the Law of Cosines for 3-link planar inverse kinematics:

```
For a 3-link arm (L2, L3, L4):
1. Project target to vertical plane: R = sqrt(x^2 + y^2), H = z - L1
2. Solve using law of cosines: cos(theta3) = (L2^2 + L34^2 - R^2 - H^2) / (2*L2*L34)
3. Compute shoulder and wrist angles from geometry
4. Base rotation: theta1 = atan2(y, x)
```

---

## Support and Contributing

### Reporting Issues

When reporting issues, include:

1. System information (OS, Python version, ROS 2 distribution)
2. Complete error message and stack trace
3. Steps to reproduce
4. Configuration (link lengths, camera parameters)
5. Log output from all nodes

### Getting Help

1. Check [Troubleshooting](#troubleshooting) section
2. Review [QUICK_START.md](QUICK_START.md) for common tasks
3. Consult [REFACTORING_SUMMARY.md](REFACTORING_SUMMARY.md) for architecture details
4. Check ROS 2 official documentation

### Contributing

Contributions are welcome. Please ensure:

1. Code follows PEP 8 style guidelines
2. All parameters are documented
3. Error handling is robust
4. Logging is comprehensive
5. Tests are included for new features

---

## License

This project is licensed under the Apache License 2.0. See LICENSE file for details.

---

## Project Information

- **Maintainer**: Robotics Team
- **Created**: April 25, 2026
- **ROS 2 Distribution**: Humble
- **Python Version**: 3.10+
- **License**: Apache-2.0

---

## Quick Command Reference

```bash
# Build
colcon build

# Source
source install/setup.bash

# Launch complete system
ros2 launch control_pkg manipulator_system_launch.py

# Monitor topics
ros2 topic list
ros2 topic echo /servo_angles

# View nodes
ros2 node list
ros2 node info /controller_node

# Set parameters
ros2 param set /controller_node angle_max_safe 170.0

# Docker build
docker-compose build

# Docker run
docker-compose up -it

# Inside Docker, launch system
ros2 launch control_pkg manipulator_system_launch.py
```

---

For detailed technical information, please refer to the documentation files included in the project.
