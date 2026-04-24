# syntax=docker/dockerfile:1
FROM ros:humble-ros-base

ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8
ENV ROS_DISTRO=humble

WORKDIR /workspace

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    python3-colcon-common-extensions \
    python3-pip \
    python3-opencv \
    python3-numpy \
    python3-rosdep \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install -U pip setuptools

COPY . /workspace

RUN rosdep init || true \
    && rosdep update || true \
    && rosdep install --from-paths src --ignore-src -r -y || true

RUN . /opt/ros/$ROS_DISTRO/setup.sh && colcon build --symlink-install

COPY ros_entrypoint.sh /ros_entrypoint.sh
RUN chmod +x /ros_entrypoint.sh

ENTRYPOINT ["/ros_entrypoint.sh"]
CMD ["bash"]
