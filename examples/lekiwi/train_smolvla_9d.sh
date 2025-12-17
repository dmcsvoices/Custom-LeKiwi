#!/bin/bash
# Training script for SmolVLA with 9D actions (arm + base)
#
# This fixes the issue where the model was only trained on 6D actions (arm only).
# The fix in src/lerobot/policies/factory.py ensures that when training from a
# pretrained model, the input/output features are overridden to match the dataset
# dimensions (9D in this case: 6 arm joints + 3 base velocities).
#
# The pretrained smolvla_base model was trained on 6D actions, but by loading a
# dataset with 9D actions, the model will adapt to the new action space. The
# pretrained vision encoder and language model weights will still be used, but
# the action prediction head will be reinitialized for 9D outputs.

lerobot-train \
  --policy.path=lerobot/smolvla_base \
  --policy.repo_id=<hf_username>/<policy_repo_name> \
  --dataset.repo_id=<hf_username>/<dataset_repo_name>  \
  --batch_size=64 \
  --steps=10000 \
  --output_dir=outputs/train/3cam_smolvla_lekiwi_PickNPlace_YellowDuck \
  --job_name=3cam_lekiwi_mobile_smolvla_9d_training \
  --policy.device=mps \
  --rename_map='{"observation.images.camera1": "observation.images.front", "observation.images.camera2": "observation.images.wrist", "observation.images.camera3": "observation.images.top"}' \
  --wandb.enable=true
