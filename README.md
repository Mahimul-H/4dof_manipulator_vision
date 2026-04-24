# 4-DOF Manipulator Vision

Docker support for the ROS2 workspace.

## Build Docker image

```bash
docker build -t manipulator-vision:latest .
```

## Run a shell inside the container

```bash
docker run --rm -it \
  -v "$(pwd)":/workspace \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  -e DISPLAY=$DISPLAY \
  --device /dev/video0 \
  --network host \
  manipulator-vision:latest
```

## Run the detector node

```bash
docker run --rm -it \
  -v "$(pwd)":/workspace \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  -e DISPLAY=$DISPLAY \
  --device /dev/video0 \
  --network host \
  manipulator-vision:latest \
  ros2 run vision_pkg detector
```

## Run the calibrator node

```bash
docker run --rm -it \
  -v "$(pwd)":/workspace \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  -e DISPLAY=$DISPLAY \
  --device /dev/video0 \
  --network host \
  manipulator-vision:latest \
  ros2 run vision_pkg calibrator
```

## Docker Compose

Start a shell session in the container:

```bash
docker-compose up --build
```

Run a node from the compose service:

```bash
docker-compose run --rm manipulator-vision ros2 run vision_pkg detector
```

## Notes

- The container sources ROS 2 Humble and the workspace install overlay automatically.
- For camera access, map `/dev/video0` from the host into the container.
- GUI windows require X11 forwarding via `DISPLAY` and `/tmp/.X11-unix`.
