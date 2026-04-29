from setuptools import setup

package_name = 'jazzy_mecanum_driver'

setup(
    name=package_name,
    version='0.0.1',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='plancaster',
    maintainer_email='plancaster@scu.edu',
    description='Single-file ROS 2 Jazzy mecanum drive node',
    license='TODO',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'jazzy_mecanum_driver = jazzy_mecanum_driver.jazzy_mecanum_driver:main',
        ],
    },
)
