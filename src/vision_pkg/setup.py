from setuptools import find_packages, setup

package_name = 'vision_pkg'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='cypher',
    maintainer_email='user@todo.com',
    description='Vision package for 4-DOF manipulator',
    license='Apache-2.0',
    entry_points={
        'console_scripts': [
            'calibrator = vision_pkg.color_calibrator:main',
            'detector = vision_pkg.object_detector.main',
        ],
    },
)
