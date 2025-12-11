#!/usr/bin/env python
"""
Analyze whether base movements were recorded in the dataset.
"""

import torch
from lerobot.datasets.lerobot_dataset import LeRobotDataset

DATASET_ID = "fruityapplebottom/3_cam_pick_up_die_50"

print(f"Loading dataset: {DATASET_ID}")
dataset = LeRobotDataset(DATASET_ID)

print(f"Analyzing {len(dataset)} frames...\n")

# Check statistics for base velocities
non_zero_x = 0
non_zero_y = 0
non_zero_theta = 0
max_x_vel = 0.0
max_y_vel = 0.0
max_theta_vel = 0.0

# Sample every 100th frame to speed up analysis
for i in range(0, len(dataset), 100):
    sample = dataset[i]
    action = sample['action']

    # Base velocities are indices 6, 7, 8
    x_vel = abs(action[6].item())
    y_vel = abs(action[7].item())
    theta_vel = abs(action[8].item())

    if x_vel > 0.001:
        non_zero_x += 1
        max_x_vel = max(max_x_vel, x_vel)
    if y_vel > 0.001:
        non_zero_y += 1
        max_y_vel = max(max_y_vel, y_vel)
    if theta_vel > 0.001:
        non_zero_theta += 1
        max_theta_vel = max(max_theta_vel, theta_vel)

samples_checked = len(range(0, len(dataset), 100))

print(f"Results (checked {samples_checked} frames):")
print(f"  Non-zero x.vel: {non_zero_x}/{samples_checked} ({100*non_zero_x/samples_checked:.1f}%)")
print(f"  Non-zero y.vel: {non_zero_y}/{samples_checked} ({100*non_zero_y/samples_checked:.1f}%)")
print(f"  Non-zero theta.vel: {non_zero_theta}/{samples_checked} ({100*non_zero_theta/samples_checked:.1f}%)")
print(f"\nMax velocities observed:")
print(f"  Max x.vel: {max_x_vel:.4f} m/s")
print(f"  Max y.vel: {max_y_vel:.4f} m/s")
print(f"  Max theta.vel: {max_theta_vel:.4f} deg/s")

if non_zero_x == 0 and non_zero_y == 0 and non_zero_theta == 0:
    print("\n⚠️  WARNING: NO BASE MOVEMENTS DETECTED IN DATASET!")
    print("   The base velocities are all zero.")
    print("   This explains why the model only learned 6D actions (arm only).")
else:
    print(f"\n✓ Base movements ARE present in the dataset")
