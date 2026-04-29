from setuptools import setup, find_packages
import os
from glob import glob

package_name = 'misc'

setup(
    name=package_name,
    version='0.0.1',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'),   glob('launch/*.launch.py')),
        (os.path.join('share', package_name, 'config'),   glob('config/*.yaml')),
        (os.path.join('share', package_name, 'rviz'),     glob('rviz/*.rviz')),
        (os.path.join('share', package_name, 'maps'),     glob('maps/*')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='agent3',
    maintainer_email='benjbanh@gmail.com',
    description='Navigation, CoM, and SLAM launch infrastructure',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'global_ref_nav   = misc.global_ref_nav:main',
            'center_of_mass   = misc.center_of_mass:main',
            'slam_pose_relay  = misc.slam_pose_relay:main',
        ],
    },
)
