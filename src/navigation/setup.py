import os
from glob import glob
from setuptools import find_packages, setup

package_name = 'navigation'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'),
            glob(os.path.join('launch', '*.py'))),
        (os.path.join('share', package_name, 'config'),
            glob(os.path.join('config', '*.yaml')) +
            glob(os.path.join('config', '*.xml')) +
            glob(os.path.join('config', '*.sh'))),
        (os.path.join('share', package_name, 'config', 'maps'),
            glob(os.path.join('config', 'maps', '*'))),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='agent1',
    maintainer_email='benjbanh@gmail.com',
    description='Multi-robot bringup: AMCL localization with shared map frame',
    license='Apache-2.0',
    extras_require={'test': ['pytest']},
    entry_points={
        'console_scripts': [
            'pose_aggregator = navigation.pose_aggregator:main',
            'robot_pose_broadcaster = navigation.robot_pose_broadcaster:main',
            'pose_normalizer = navigation.pose_normalizer:main',
            'aggregation = navigation.aggregation:main',
            'formation_control = navigation.formation_control:main',
            'formation_control_3 = navigation.formation_control_3:main',
        ],
    },
)
