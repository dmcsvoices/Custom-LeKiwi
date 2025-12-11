# Fix: Training with 9D Actions (Arm + Base)

## Problem Summary

The model `fruityapplebottom/SmolVLA_3cam_LeKiwi_Mobile_B` was trained with only **6D actions** (arm joints only), even though the dataset `fruityapplebottom/3_cam_pick_up_die_50` contains **9D actions** (6 arm joints + 3 base velocities).

### Root Cause

When loading a pretrained model (like `lerobot/smolvla_base`), the training code was **not overriding** the input/output features from the dataset. Instead, it kept the pretrained model's features (6D), ignoring the dataset's 9D action space.

In `src/lerobot/policies/factory.py:403-406`, the original code was:

```python
if not cfg.output_features:  # Only set if not already set
    cfg.output_features = {...}
if not cfg.input_features:   # Only set if not already set
    cfg.input_features = {...}
```

When loading `lerobot/smolvla_base` (which has 6D features), these features were already set, so they were never overridden with the dataset's 9D features.

## The Fix

### Code Changes

**File**: `src/lerobot/policies/factory.py` (lines 403-409)

**Before**:
```python
if not cfg.output_features:
    cfg.output_features = {key: ft for key, ft in features.items() if ft.type is FeatureType.ACTION}
if not cfg.input_features:
    cfg.input_features = {key: ft for key, ft in features.items() if key not in cfg.output_features}
```

**After**:
```python
# IMPORTANT: Always override features from dataset/env, even for pretrained models
# This ensures that if you train on a dataset with different action dimensions than
# the pretrained model (e.g., 9D vs 6D), the model will adapt to the new dimensions
if not cfg.output_features or (ds_meta is not None and cfg.pretrained_path):
    cfg.output_features = {key: ft for key, ft in features.items() if ft.type is FeatureType.ACTION}
if not cfg.input_features or (ds_meta is not None and cfg.pretrained_path):
    cfg.input_features = {key: ft for key, ft in features.items() if key not in cfg.output_features}
```

### What This Does

The fix ensures that when training from a pretrained model (`cfg.pretrained_path` is set) with a dataset (`ds_meta is not None`), the input/output features are **always overridden** to match the dataset's dimensions.

This means:
- ✅ Pretrained vision encoder weights are kept
- ✅ Pretrained language model weights are kept
- ✅ Action prediction head is **reinitialized** for the new action space (9D)
- ✅ Model will train on all 9 dimensions from the dataset

## Verification

Run the verification script to confirm the fix works:

```bash
cd examples/lekiwi
python verify_9d_training.py
```

Expected output:
```
✓ SUCCESS: Model configured with 9D actions
  ✓ Correct! Model will train on all 9 dimensions (6 arm + 3 base)
```

## Training a New 9D Model

### Option 1: Use the Updated Training Script

```bash
cd examples/lekiwi
bash train_smolvla.sh
```

This script now automatically uses 9D actions from the dataset.

### Option 2: Use the Dedicated 9D Training Script

```bash
cd examples/lekiwi
bash train_smolvla_9d.sh
```

Both scripts will now correctly train with:
- **Input state**: 9 dimensions (6 arm joints + 3 base velocities)
- **Output actions**: 9 dimensions (6 arm joints + 3 base velocities)

### Training Configuration

The model will be saved to a new HuggingFace repo:
- **New model**: `fruityapplebottom/SmolVLA_3cam_LeKiwi_Mobile_9D`
- **Old model** (6D only): `fruityapplebottom/SmolVLA_3cam_LeKiwi_Mobile_B`

Training parameters:
- Batch size: 64
- Steps: 20,000
- Device: MPS (Apple Silicon)
- Pretrained base: `lerobot/smolvla_base` (vision/language weights transferred)

## Dataset Analysis

The dataset `fruityapplebottom/3_cam_pick_up_die_50` analysis shows:

- **Total frames**: 45,000
- **Episodes**: 50
- **Action dimensions**: 9

Base movement statistics:
- **Non-zero x.vel**: ~4.9% of frames (forward/backward)
- **Non-zero y.vel**: ~0.4% of frames (strafe)
- **Non-zero theta.vel**: ~4.9% of frames (rotation)

Base movements were recorded but sparse. This is normal for tasks where the robot primarily uses the arm, with occasional base repositioning.

## Evaluation

### Using the Old 6D Model

The old model can still be used with the `ActionPaddingWrapper` in `examples/lekiwi/evaluate.py`:

```python
base_policy = SmolVLAPolicy.from_pretrained("fruityapplebottom/SmolVLA_3cam_LeKiwi_Mobile_B")
policy = ActionPaddingWrapper(base_policy, target_action_dim=9)
```

This pads the 6D output with zeros for base velocities, so the robot can move the arm but the base will remain stationary.

### Using the New 9D Model

Once you train the new model, update `evaluate.py`:

```python
# No wrapper needed - model outputs 9D actions directly
policy = SmolVLAPolicy.from_pretrained("fruityapplebottom/SmolVLA_3cam_LeKiwi_Mobile_9D")
```

The model will control both arm and base movements.

## Impact

### Before Fix
- ❌ Model trained on 6D actions only
- ❌ Base velocities ignored during training
- ❌ Robot base doesn't move during evaluation
- ❌ Required workaround (ActionPaddingWrapper)

### After Fix
- ✅ Model trains on full 9D action space
- ✅ Base velocities learned from data
- ✅ Robot can control both arm and base
- ✅ No workarounds needed

## Additional Notes

### Why Was the Base Movement Sparse?

The dataset shows only ~5% of frames have non-zero base movement. This is actually **correct** for this task:

1. The task is "Pick up the die" - primarily an arm manipulation task
2. Base movement is only needed occasionally for repositioning
3. The robot likely started in a good position for most episodes

For tasks requiring more base movement:
- Record demonstrations with more deliberate base repositioning
- Aim for >20% of frames with base movement
- Consider separate episodes for base-heavy vs arm-heavy tasks

### SmolVLA Action Padding

SmolVLA pads actions internally to `max_action_dim=32`. The model can handle any action dimension up to 32, so 9D is well within its capabilities.

## Files Changed

1. **src/lerobot/policies/factory.py** - Core fix for feature override
2. **examples/lekiwi/train_smolvla.sh** - Updated with 9D training
3. **examples/lekiwi/train_smolvla_9d.sh** - New dedicated 9D training script
4. **examples/lekiwi/verify_9d_training.py** - Verification script
5. **examples/lekiwi/evaluate.py** - ActionPaddingWrapper for old 6D model
6. **examples/lekiwi/check_dataset_actions.py** - Dataset analysis tool
7. **examples/lekiwi/analyze_base_movement.py** - Base movement analysis tool

## Testing Checklist

- [x] Verified dataset has 9D actions
- [x] Verified base movements are present (sparse but recorded)
- [x] Fixed feature override in factory.py
- [x] Verified fix works with verify_9d_training.py
- [x] Updated training scripts
- [x] Created evaluation workaround for old model
- [ ] Train new 9D model
- [ ] Evaluate new model on real robot
- [ ] Confirm base movements are executed
