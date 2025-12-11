<p align="center">
  <img alt="Custom LeKiwi - Enhanced Dual Motor Controller Support" src="https://raw.githubusercontent.com/huggingface/lerobot/main/media/lekiwi/kiwi.webp" width="60%">
  <br/>
  <br/>
</p>

<div align="center">

[![Based on LeRobot](https://img.shields.io/badge/Based%20on-LeRobot-blue)](https://github.com/huggingface/lerobot)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

</div>

<h1 align="center">Custom LeKiwi - Dual Motor Controller Edition</h1>

<h3 align="center">
    <p>Enhanced LeKiwi with support for dual motor control boards</p>
    <p>Mix 12V and 7V servos for optimal performance! ⚡</p>
</h3>

---

## 🚀 What's Different?

This is a **custom fork** of the [HuggingFace LeRobot](https://github.com/huggingface/lerobot) project, specifically enhanced for the **LeKiwi mobile robot** with **dual motor control board support**.

### Key Enhancements

#### 1. Dual Motor Controller Architecture

The standard LeKiwi assumes all motors (arm + base) are connected to a **single motor control board**. This fork adds support for **two independent motor control boards**, enabling:

✅ **Voltage Flexibility**: Mix 12V servos (arm) and 7V servos (base) on separate boards
✅ **Power Management**: Isolate power domains for arm and base motors
✅ **Better Performance**: Dedicated control board per motor group reduces communication overhead
✅ **Auto-Detection**: Automatically detects which USB port has which board
✅ **Backwards Compatible**: Single-board mode still works perfectly

#### 2. 9D Action Space for Mobile Manipulation 🆕

This fork includes critical fixes for training models with **full 9D action control** (6 arm joints + 3 base velocities):

✅ **Full Mobile Manipulation**: Train models that control both arm AND base simultaneously
✅ **6D→9D Model Adaptation**: Fine-tune pretrained arm-only models for full robot control
✅ **Automatic Feature Override**: Policy factory correctly handles action space mismatches
✅ **3-Camera Vision**: Multi-camera support for better spatial awareness

### Why This Matters

**Standard LeKiwi Limitation:**
- All 9 motors on one control board
- Single voltage rail (typically 7V or 12V, not both)
- Motor IDs 1-6 (arm) and 7-9 (base) share the same bus

**This Fork's Solution:**
- **Board 1**: Motors 1-6 (arm motors) @ **12V** for torque
- **Board 2**: Motors 7-9 (base wheels) @ **7V** for speed
- Independent USB connections (`/dev/ttyACM0` and `/dev/ttyACM1`)
- Automatic port detection with manual override option

---

## 📋 Table of Contents

- [Dual Board Setup](#-dual-board-setup)
- [Installation](#-installation)
- [Quick Start](#-quick-start)
- [Calibration](#-calibration)
- [Teleoperation](#-teleoperation)
- [Training with 9D Actions](#-training-with-9d-actions)
- [Troubleshooting](#-troubleshooting)
- [Original LeRobot Features](#-original-lerobot-features)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🔧 Dual Board Setup

### Hardware Requirements

**Motor Control Boards:**
- 2× Feetech SCS motor control boards (or compatible)
- Separate power supplies for each board (recommended: 12V for arm, 7V for base)

**Motors:**
- **Arm Motors (IDs 1-6)**: Connect to Board 1
  - Motor 1: arm_shoulder_pan
  - Motor 2: arm_shoulder_lift
  - Motor 3: arm_elbow_flex
  - Motor 4: arm_wrist_flex
  - Motor 5: arm_wrist_roll
  - Motor 6: arm_gripper
- **Base Motors (IDs 7-9)**: Connect to Board 2
  - Motor 7: base_left_wheel
  - Motor 8: base_back_wheel
  - Motor 9: base_right_wheel

**Connections:**
- Board 1 (Arm) → USB → `/dev/ttyACM0` or `/dev/ttyACM1` (auto-detected)
- Board 2 (Base) → USB → `/dev/ttyACM0` or `/dev/ttyACM1` (auto-detected)

### Software Configuration

Enable dual board mode by adding `--robot.use_dual_boards=true` to any LeKiwi command:

```bash
# Auto-detection (recommended)
lerobot-calibrate \
    --robot.type=lekiwi \
    --robot.id=my_awesome_kiwi \
    --robot.use_dual_boards=true
```

**Manual Port Assignment** (if auto-detection fails):

```bash
lerobot-calibrate \
    --robot.type=lekiwi \
    --robot.id=my_awesome_kiwi \
    --robot.use_dual_boards=true \
    --robot.arm_port=/dev/ttyACM0 \
    --robot.base_port=/dev/ttyACM1
```

### Port Auto-Detection

The system automatically detects which USB port has which board by:
1. Scanning `/dev/ttyACM0` and `/dev/ttyACM1`
2. Pinging Motor ID 1 (arm_shoulder_pan) on each port
3. Assigning ports based on which responds

**Note:** USB port assignments can change when cables are unplugged/replugged. Auto-detection handles this automatically.

---

## 📦 Installation

### Prerequisites

- Python 3.10 or higher
- Linux-based system (tested on Ubuntu 22.04 / Raspberry Pi OS)
- USB permissions for serial devices

### Environment Setup

Create a virtual environment with Python 3.10:

```bash
conda create -y -n lerobot python=3.10
conda activate lerobot
```

Install `ffmpeg` (required for video recording):

```bash
conda install ffmpeg -c conda-forge
```

### Install This Fork

Clone this repository and install:

```bash
git clone https://github.com/dmcsvoices/Custom-LeKiwi.git
cd Custom-LeKiwi
pip install -e .
```

> **NOTE:** If you encounter build errors, install additional dependencies:
> ```bash
> sudo apt-get install cmake build-essential python3-dev pkg-config \
>     libavformat-dev libavcodec-dev libavdevice-dev libavutil-dev \
>     libswscale-dev libswresample-dev libavfilter-dev
> ```

### USB Permissions

Add your user to the `dialout` group for serial port access:

```bash
sudo usermod -aG dialout $USER
```

**Important:** Log out and log back in for this to take effect.

---

## 🚦 Quick Start

### 1. Setup Motor IDs

**For Dual Board Setup:**

```bash
lerobot-setup-motors \
    --robot.type=lekiwi \
    --robot.use_dual_boards=true
```

This will guide you through:
1. Setting up arm motors (IDs 1-6) on Board 1
2. Setting up base motors (IDs 7-9) on Board 2

**For Single Board Setup** (backwards compatible):

```bash
lerobot-setup-motors --robot.type=lekiwi
```

### 2. Calibrate the Robot

**Dual Board Mode:**

```bash
lerobot-calibrate \
    --robot.type=lekiwi \
    --robot.id=my_awesome_kiwi \
    --robot.use_dual_boards=true
```

Follow the prompts to:
1. Position arm at mid-range
2. Move all joints through their full range
3. Calibration is saved automatically

**Single Board Mode:**

```bash
lerobot-calibrate \
    --robot.type=lekiwi \
    --robot.id=my_awesome_kiwi
```

### 3. Test Teleoperation

**Terminal 1 (Robot Host):**

```bash
python -m lerobot.robots.lekiwi.lekiwi_host \
    --robot.id=my_awesome_kiwi \
    --robot.use_dual_boards=true \
    --host.connection_time_s=600
```

**Terminal 2 (Control Options):**

**Xbox Controller (Recommended):**
```bash
pip install approxeng.input
python examples/lekiwi/teleoperate_xbox_controller.py
```
- Analog joystick control
- Speed boost/slow with triggers
- See [full guide](examples/lekiwi/README_XBOX_CONTROLLER.md)

**OR Keyboard:**
```bash
python examples/lekiwi/teleoperate_keyboard_only.py
```
- `w/s` - forward/backward
- `a/d` - strafe left/right
- `z/x` - rotate left/right
- `r/f` - increase/decrease speed
- `q` - quit

Edit `ROBOT_IP` in either script:
- Use `"localhost"` if running on the same machine
- Use your robot's IP (e.g., `"192.168.1.100"`) if running remotely

---

## 🎯 Calibration

Calibration establishes motor ranges and homing positions. It must be done once per robot or when motors are replaced.

### Calibration Process

1. **Start calibration:**
   ```bash
   lerobot-calibrate \
       --robot.type=lekiwi \
       --robot.id=my_awesome_kiwi \
       --robot.use_dual_boards=true
   ```

2. **Position robot:** Move the arm to the middle of its range of motion, then press ENTER

3. **Record ranges:** Move each joint through its full range. The system records min/max positions automatically. Press ENTER when done.

4. **Save:** Calibration is automatically saved to `.cache/calibration/lekiwi/my_awesome_kiwi.json`

### Using Existing Calibration

If a calibration file exists, you'll be prompted:
- Press **ENTER** to use existing calibration
- Type **'c'** and press ENTER to run new calibration

### Calibration Files

Calibration is stored in: `~/.cache/calibration/lekiwi/<robot_id>.json`

To share calibration between setups, copy this file.

---

## 🎮 Teleoperation

### Host + Client Setup (Recommended)

**On the Robot (Raspberry Pi):**

```bash
python -m lerobot.robots.lekiwi.lekiwi_host \
    --robot.id=my_awesome_kiwi \
    --robot.use_dual_boards=true \
    --host.connection_time_s=600 \
    --host.watchdog_timeout_ms=1000
```

**On Your Laptop:**

**Option 1: Xbox Controller (Recommended)**
```bash
# Install controller support
pip install approxeng.input

# Run Xbox controller teleoperation
python examples/lekiwi/teleoperate_xbox_controller.py
```
- Analog control with joysticks
- Speed boost/slow mode with triggers
- Emergency stop with B button
- See [Xbox Controller Guide](examples/lekiwi/README_XBOX_CONTROLLER.md) for full documentation

**Option 2: Keyboard**
```bash
python examples/lekiwi/teleoperate_keyboard_only.py
```
- Digital control (WASD + ZX for rotation)
- Good for testing without controller

**Option 3: Full Arm + Base (SO100 Leader)**
```bash
python examples/lekiwi/teleoperate.py
```
- Requires SO100 leader arm for full control

### Configuration Options

**Connection Time:**
- Default: 30 seconds
- Recommended for testing: 600 seconds (10 minutes)
- Adjust with `--host.connection_time_s=<seconds>`

**Watchdog Timeout:**
- Default: 500 ms
- Stops base motors if no command received
- Adjust with `--host.watchdog_timeout_ms=<milliseconds>`

---

## 🎓 Training with 9D Actions

### Overview

This fork includes critical fixes that enable training models with **full 9D action space** control (6 arm joints + 3 base velocities). Previously, models trained from pretrained checkpoints would ignore base velocities and only learn arm control.

### The Problem (Now Fixed!)

**Before this fix:**
- When fine-tuning a pretrained arm-only model (6D) with a dataset containing arm+base data (9D)
- The policy factory would keep the pretrained model's 6D action space
- Base velocities (`x.vel`, `y.vel`, `theta.vel`) were **ignored during training**
- Result: Models could only control the arm, not the base

**After this fix:**
- Policy factory automatically detects action dimension mismatches
- Overrides input/output features to match the dataset's action space
- Vision and language model weights are preserved from pretrained checkpoint
- Action prediction head is reinitialized for the new 9D action space
- Result: Models learn to control **both arm AND base**

### Action Space Format

**6D Actions** (Arm Only):
```python
{
    "arm_shoulder_pan": float,   # radians
    "arm_shoulder_lift": float,  # radians
    "arm_elbow_flex": float,     # radians
    "arm_wrist_flex": float,     # radians
    "arm_wrist_roll": float,     # radians
    "arm_gripper": float,        # -1.0 to 1.0
}
```

**9D Actions** (Full Mobile Manipulation):
```python
{
    "arm_shoulder_pan": float,   # radians
    "arm_shoulder_lift": float,  # radians
    "arm_elbow_flex": float,     # radians
    "arm_wrist_flex": float,     # radians
    "arm_wrist_roll": float,     # radians
    "arm_gripper": float,        # -1.0 to 1.0
    "x.vel": float,              # m/s (forward/backward)
    "y.vel": float,              # m/s (strafe left/right)
    "theta.vel": float,          # deg/s (rotation)
}
```

### Training with 9D Actions

**Step 1: Record Dataset with Base Movement**

Ensure your demonstrations include base movement:

```bash
# Record with Xbox controller (arm + base control)
python examples/lekiwi/record_xbox_hybrid.py
```

**Step 2: Verify Dataset Contains 9D Actions**

```bash
# Check dataset action dimensions
python examples/lekiwi/check_dataset_actions.py

# Analyze base movement statistics
python examples/lekiwi/analyze_base_movement.py
```

Expected output:
```
✓ Dataset contains 9D actions
✓ Base movement detected in X% of frames
```

**Step 3: Train with Pretrained Model**

The fix in `src/lerobot/policies/factory.py` automatically handles dimension adaptation:

```bash
python lerobot/scripts/train.py \
    --policy.type=smolvla \
    --policy.pretrained_path=lerobot/smolvla_base \
    --dataset.repo_id=your_username/your_9d_dataset \
    --training.batch_size=64 \
    --training.num_steps=20000
```

**What happens automatically:**
1. ✅ Pretrained vision encoder loaded (frozen or fine-tuned)
2. ✅ Pretrained language model loaded (frozen or fine-tuned)
3. ✅ Action prediction head **reinitialized** for 9D output
4. ✅ Model trains on all 9 dimensions from your dataset

**Step 4: Verify Training Configuration**

```bash
# Verify model is configured for 9D
python examples/lekiwi/verify_9d_training.py
```

Expected output:
```
✓ SUCCESS: Model configured with 9D actions
  ✓ Output features: 9 dimensions
  ✓ Will train on: 6 arm joints + 3 base velocities
```

### Using 6D Models with 9D Robot

If you already have a trained 6D model and want to use it with the 9D robot, use the `ActionPaddingWrapper`:

```python
from lerobot.policies.smolvla.modeling_smolvla import SmolVLAPolicy

# Load 6D arm-only model
base_policy = SmolVLAPolicy.from_pretrained("your_username/arm_only_model")

# Wrap to pad 6D output to 9D (base velocities will be zero)
from examples.lekiwi.evaluate import ActionPaddingWrapper
policy = ActionPaddingWrapper(base_policy, target_action_dim=9)

# Use with robot - arm will move, base will stay stationary
```

**Note:** The wrapped model can control the arm but **not** the base. To get base control, you must train a model with 9D data.

### 3-Camera Configuration

This fork also includes corrected 3-camera support for better spatial awareness:

**Camera Setup:**
- **Front camera**: `/dev/video2` - Wide view of workspace (rotated 270°)
- **Wrist camera**: `/dev/video0` - End-effector view (rotated 90°)
- **Top camera**: `/dev/video4` - Bird's eye view (rotated 90°)

Configuration is in `src/lerobot/robots/lekiwi/config_lekiwi.py`.

### Documentation

For detailed technical information about the 9D action space fix, see:
- [`FIX_9D_ACTIONS.md`](FIX_9D_ACTIONS.md) - Complete technical explanation
- [`CLAUDE.md`](CLAUDE.md) - Comprehensive development guide
- [`examples/lekiwi/verify_9d_training.py`](examples/lekiwi/verify_9d_training.py) - Verification script

### Example Training Script

```bash
#!/bin/bash
# Train SmolVLA with 9D actions for mobile manipulation

python lerobot/scripts/train.py \
    --policy.type=smolvla \
    --policy.pretrained_path=lerobot/smolvla_base \
    --dataset.repo_id=your_username/mobile_manipulation_dataset \
    --dataset.image_keys="front,wrist,top" \
    --training.batch_size=64 \
    --training.num_steps=20000 \
    --training.save_freq=5000 \
    --training.eval_freq=5000 \
    --training.log_freq=100 \
    --device=cuda \
    --wandb.enable=true \
    --wandb.project=lekiwi-mobile-manipulation
```

### Key Takeaways

✅ **This fork automatically handles 6D→9D adaptation** when training
✅ **No manual configuration needed** - the fix is transparent
✅ **Pretrained weights are preserved** for vision and language models
✅ **Base movement will be learned** if present in your dataset
✅ **Verification tools included** to confirm 9D training setup

---

## 🔍 Troubleshooting

### Port Auto-Detection Fails

**Error:** `Could not auto-detect motor control boards`

**Solutions:**
1. **Check connections:** Ensure both boards are powered and connected via USB
2. **Verify motor IDs:** Use `lerobot-setup-motors` to confirm Motor ID 1 exists on arm board
3. **Manual assignment:**
   ```bash
   lerobot-calibrate \
       --robot.type=lekiwi \
       --robot.id=my_awesome_kiwi \
       --robot.use_dual_boards=true \
       --robot.arm_port=/dev/ttyACM0 \
       --robot.base_port=/dev/ttyACM1
   ```

### USB Ports Swap After Reboot

**Issue:** Ports change from `/dev/ttyACM0` ↔ `/dev/ttyACM1`

**Solution:** Auto-detection handles this automatically! No action needed.

**Alternative:** Create persistent udev rules:
```bash
# Identify boards by serial number or USB port
ls -l /dev/serial/by-id/
```

### Permission Denied on Serial Ports

**Error:** `Permission denied: '/dev/ttyACM0'`

**Solution:**
```bash
sudo usermod -aG dialout $USER
# Log out and log back in
```

### Teleoperation Ends Too Quickly

**Issue:** "Command not received" warnings, host shuts down after 30 seconds

**Solution:** Increase connection timeout:
```bash
python -m lerobot.robots.lekiwi.lekiwi_host \
    --robot.id=my_awesome_kiwi \
    --robot.use_dual_boards=true \
    --host.connection_time_s=600
```

### Motors Don't Respond

**Check:**
1. **Power:** Both boards have power supplies connected
2. **Motor IDs:** Run `lerobot-setup-motors` to verify IDs
3. **Connections:** Motors properly connected to correct board
4. **Calibration:** Run calibration again

**Test individual boards:**
```bash
# Test arm board only (single board mode)
lerobot-calibrate --robot.type=lekiwi --robot.id=test_arm --robot.port=/dev/ttyACM0
```

---

## 📚 Original LeRobot Features

This fork maintains **full compatibility** with all LeRobot features:

### State-of-the-Art AI for Real-World Robotics

🤗 LeRobot provides models, datasets, and tools for real-world robotics in PyTorch, with:
- Imitation learning and reinforcement learning approaches
- Pretrained models and datasets
- Simulation environments
- Hugging Face Hub integration

### Supported Robots

- **SO-101 / SO-100**: Low-cost robotic arm (~€114)
- **HopeJR**: Humanoid arm and hand for dexterous manipulation
- **LeKiwi**: Mobile manipulation platform (this fork!)
- **ALOHA**: Bimanual manipulation system
- **And more...**

### Key Features

- **🤖 Multiple Robot Support**: SO-101, ALOHA, LeKiwi, and more
- **🎓 State-of-the-Art Policies**: ACT, Diffusion Policy, TDMPC
- **📊 Dataset Management**: Easy upload/download from Hugging Face Hub
- **🎥 Video Recording**: Automatic episode recording with multiple cameras
- **📈 Training**: Built-in training pipelines with WandB integration
- **🔄 Simulation**: Gymnasium environments for testing

### Documentation & Resources

- **Original Project:** [github.com/huggingface/lerobot](https://github.com/huggingface/lerobot)
- **Documentation:** [huggingface.co/docs/lerobot](https://huggingface.co/docs/lerobot)
- **LeKiwi Tutorial:** [huggingface.co/docs/lerobot/lekiwi](https://huggingface.co/docs/lerobot/lekiwi)
- **Datasets:** [huggingface.co/lerobot](https://huggingface.co/lerobot)
- **Discord Community:** [discord.gg/s3KuuzsPFb](https://discord.gg/s3KuuzsPFb)

---

## 📖 Implementation Details

### Architecture Overview

**Single Board Mode** (original):
```
/dev/ttyACM0 → FeetechMotorsBus → All 9 motors (IDs 1-9)
```

**Dual Board Mode** (this fork):
```
/dev/ttyACM0 → arm_bus → Arm motors (IDs 1-6)
/dev/ttyACM1 → base_bus → Base motors (IDs 7-9)
```

### Files Modified

1. **`src/lerobot/robots/lekiwi/config_lekiwi.py`**
   - Added `use_dual_boards`, `arm_port`, `base_port` parameters

2. **`src/lerobot/robots/lekiwi/lekiwi.py`**
   - Dual bus initialization and routing
   - Port auto-detection
   - Updated all methods (connect, calibrate, get_observation, send_action, etc.)

3. **`examples/lekiwi/teleoperate_keyboard_only.py`**
   - Simplified teleoperation script for testing (keyboard only, no leader arm)

### Technical Documentation

For detailed implementation information, see:
- [`DUAL_BOARD_IMPLEMENTATION_PLAN.md`](DUAL_BOARD_IMPLEMENTATION_PLAN.md) - Full implementation plan
- [`DUAL_BOARD_IMPLEMENTATION_SUMMARY.md`](DUAL_BOARD_IMPLEMENTATION_SUMMARY.md) - Usage guide and troubleshooting

---

## 🤝 Contributing

Contributions are welcome! This fork focuses on LeKiwi dual board enhancements, but general improvements are appreciated.

### Development Setup

```bash
git clone https://github.com/dmcsvoices/Custom-LeKiwi.git
cd Custom-LeKiwi
pip install -e ".[dev]"
```

### Reporting Issues

Please include:
- LeRobot version / commit hash
- Hardware configuration (single vs dual board)
- Python version and OS
- Complete error messages and logs

### Pull Requests

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes with clear messages
4. Push to your fork
5. Open a pull request

---

## 📄 License

This project inherits the Apache 2.0 license from the original LeRobot project.

```
Copyright 2024 The HuggingFace Inc. team. All rights reserved.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
```

---

## 🙏 Acknowledgments

- **HuggingFace LeRobot Team**: For the excellent original project and LeKiwi robot design
- **Community Contributors**: For testing and feedback
- **Feetech**: For the motor control systems

---

## 📞 Support

- **Issues:** [GitHub Issues](https://github.com/dmcsvoices/Custom-LeKiwi/issues)
- **Original LeRobot Discord:** [discord.gg/s3KuuzsPFb](https://discord.gg/s3KuuzsPFb)
- **Original Docs:** [huggingface.co/docs/lerobot](https://huggingface.co/docs/lerobot)

---

<div align="center">

**⭐ Star this repo if dual motor control helps your project!**

**🔗 Based on [HuggingFace LeRobot](https://github.com/huggingface/lerobot)**

</div>
