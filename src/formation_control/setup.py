import os
from glob import glob
from setuptools import setup

package_name = 'formation_control'

setup(
    name=package_name,
    version='0.1.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='agent1',
    maintainer_email='benjbanh@gmail.com',
    description='Single-robot goto goal: drives a mecanum robot to an (x, y) position via odom feedback',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'goto_goal_node = formation_control.simple_aggregation:main',
            'simple_aggregation = formation_control.simple_aggregation:main',
        ],
    },
)
