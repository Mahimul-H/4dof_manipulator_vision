from setuptools import find_packages, setup
from glob import glob
import os

package_name = 'hardware_interface_pkg'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob(os.path.join('launch', '*.py'))),
    ],
    install_requires=['setuptools', 'rclpy', 'pyserial'],
    zip_safe=True,
    maintainer='shouptick',
    maintainer_email='hoque2131005@stud.kuet.ac.bd',
    description='Hardware interface for serial communication with Arduino',
    license='Apache-2.0',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'serial_bridge = hardware_interface_pkg.serial_bridge:main',
        ],
    },
)
