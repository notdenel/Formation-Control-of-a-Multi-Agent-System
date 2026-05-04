#!/bin/bash

# Ensure we are in a ROS 2 environment
if ! command -v ros2 &> /dev/null; then
    echo "Error: ROS 2 not found. Please source your workspace."
    exit 1
fi

echo "Collecting IMU angular velocity for 60s..."

# Use --field to get exactly what we need and pipe to awk
# '2>/dev/null' silences the "Terminated" message from the shell
timeout 60s ros2 topic echo /imu --field angular_velocity 2>/dev/null | \
awk '
    /x:/ { sumx += $2; count++ }
    /y:/ { sumy += $2 }
    /z:/ { sumz += $2 }
    END {
        if (count > 0) {
            printf "\n--- Results (60s Window) ---\n"
            printf "Samples: %d\n", count
            printf "Avg X:   %f\n", sumx / count
            printf "Avg Y:   %f\n", sumy / count
            printf "Avg Z:   %f\n", sumz / count
            printf "\n---                     ---\n"
            printf "Apply to gyro_calib in calibration/config/imu_calib\n"


        } else {
            print "\nError: No data received. Is the controller running?"
        }
    }
'