#!/usr/bin/env python
"""
Verification script to test that the 9D action training fix works.
This simulates what happens during training initialization to ensure
the model will be configured with 9D actions from the dataset.
"""

from lerobot.configs.types import PolicyFeature, FeatureType
from lerobot.datasets.lerobot_dataset import LeRobotDataset
from lerobot.policies.factory import make_policy
from lerobot.policies.smolvla.configuration_smolvla import SmolVLAConfig

# Load the dataset
DATASET_ID = "fruityapplebottom/3_cam_pick_up_die_50"
print(f"Loading dataset: {DATASET_ID}")
dataset = LeRobotDataset(DATASET_ID)

print(f"\nDataset action features:")
for key, value in dataset.features.items():
    if key.startswith("action"):
        print(f"  {key}: {value}")

# Create policy config
cfg = SmolVLAConfig(
    pretrained_path="lerobot/smolvla_base",
    device="mps",
)

print(f"\nBefore make_policy:")
print(f"  Config input_features: {cfg.input_features}")
print(f"  Config output_features: {cfg.output_features}")

# This simulates what happens in lerobot-train
print(f"\nCalling make_policy with dataset metadata...")
try:
    policy = make_policy(
        cfg=cfg,
        ds_meta=dataset.meta,
        rename_map={
            "observation.images.front": "observation.images.camera1",
            "observation.images.wrist": "observation.images.camera2",
            "observation.images.top": "observation.images.camera3"
        }
    )

    print(f"\nAfter make_policy:")
    print(f"  Policy input_features:")
    for key, value in policy.config.input_features.items():
        print(f"    {key}: {value}")

    print(f"\n  Policy output_features:")
    for key, value in policy.config.output_features.items():
        print(f"    {key}: {value}")

    # Check action dimensions
    action_feature = policy.config.output_features.get("action")
    if action_feature:
        action_dim = action_feature.shape[0] if isinstance(action_feature.shape, tuple) else action_feature.shape
        print(f"\n✓ SUCCESS: Model configured with {action_dim}D actions")

        if action_dim == 9:
            print("  ✓ Correct! Model will train on all 9 dimensions (6 arm + 3 base)")
        elif action_dim == 6:
            print("  ✗ ERROR: Model still configured for 6D actions only")
            print("  The fix did not work correctly.")
        else:
            print(f"  ⚠ WARNING: Unexpected action dimension: {action_dim}")
    else:
        print("\n✗ ERROR: No action output feature found")

except Exception as e:
    print(f"\n✗ ERROR during make_policy: {e}")
    import traceback
    traceback.print_exc()
