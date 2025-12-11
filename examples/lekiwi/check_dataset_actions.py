#!/usr/bin/env python
"""
Diagnostic script to check what actions are in a dataset.
This helps diagnose why a model might have been trained with fewer action dimensions.
"""

from lerobot.datasets.lerobot_dataset import LeRobotDataset

# The dataset the model was trained on
DATASET_ID = "fruityapplebottom/3_cam_pick_up_die_50"  # Based on rec_3Cam_50.py repo ID

print(f"Loading dataset: {DATASET_ID}")
dataset = LeRobotDataset(DATASET_ID)

print(f"\nDataset info:")
print(f"  Total frames: {len(dataset)}")
print(f"  Total episodes: {dataset.num_episodes}")
print(f"  FPS: {dataset.fps}")

print(f"\nAction features:")
for key, value in dataset.features.items():
    if key.startswith("action"):
        print(f"  {key}: {value}")

print(f"\nAction statistics:")
if hasattr(dataset, 'meta') and hasattr(dataset.meta, 'stats'):
    stats = dataset.meta.stats
    if 'action' in stats:
        action_stats = stats['action']
        print(f"  Mean shape: {action_stats['mean'].shape}")
        print(f"  Std shape: {action_stats['std'].shape}")
        print(f"  Action dimension: {action_stats['mean'].shape[0]}")

        # Print the action names if available
        print(f"\nAction names:")
        action_keys = [k for k in dataset.features.keys() if k.startswith("action")]
        for i, key in enumerate(sorted(action_keys)):
            if i < len(action_stats['mean']):
                print(f"  {i}: {key} - mean={action_stats['mean'][i]:.4f}, std={action_stats['std'][i]:.4f}")

# Sample a few frames to check action values
print(f"\nSample actions from first episode:")
for i in range(min(5, len(dataset))):
    sample = dataset[i]
    action = sample['action']
    print(f"  Frame {i}: shape={action.shape}, values={action}")
