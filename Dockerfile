# syntax=docker/dockerfile:1
FROM ros:humble-ros-base

ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8
ENV ROS_DISTRO=humble

WORKDIR /workspace

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    python3-colcon-common-extensions \
    python3-pip \
    python3-opencv \
    python3-numpy \
    python3-rosdep \
    python3-serial \
    libopencv-dev \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip and install additional Python packages
RUN pip3 install -U pip setuptools

# Copy workspace
COPY . /workspace

# Install ROS 2 dependencies
RUN rosdep init || true \
    && rosdep update || true \
    && rosdep install --from-paths src --ignore-src -r -y || true

# Build ROS 2 packages
RUN . /opt/ros/$ROS_DISTRO/setup.sh && colcon build --symlink-install

# Copy entrypoint script
COPY ros_entrypoint.sh /ros_entrypoint.sh
RUN chmod +x /ros_entrypoint.sh

ENTRYPOINT ["/ros_entrypoint.sh"]
CMD ["bash"]
