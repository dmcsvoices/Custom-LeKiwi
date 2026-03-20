# Camera Configuration Fix Guide

## Problem Summary

When you add additional cameras to the `camera_config` dictionary in `teleoperate_xbox_hybrid.py`, they get silently ignored because the robot host only sends camera data for cameras defined in the **robot's default configuration**, not the client configuration.

## Root Cause Locations

The camera filtering happens in **two separate places** that must both be configured correctly:

### 1. **Robot Host Side (SERVER)** - This is the main issue
**File**: `/src/lerobot/robots/lekiwi/config_lekiwi.py`
**Function**: `lekiwi_cameras_config()` (lines 23-31)

This function defines which cameras the robot host will actually initialize and send data for.

```python
def lekiwi_cameras_config() -> dict[str, CameraConfig]:
    return {
        "front": OpenCVCameraConfig(
            index_or_path="/dev/video2", fps=30, width=640, height=480, rotation=Cv2Rotation.NO_ROTATION
        ),
        "wrist": OpenCVCameraConfig(
            index_or_path="/dev/video0", fps=30, width=480, height=640, rotation=Cv2Rotation.NO_ROTATION
        )
    }
```

### 2. **Client Side (YOUR SCRIPT)**
**File**: `examples/lekiwi/teleoperate_xbox_hybrid.py`
**Line**: 97

Your camera_config dictionary (this you already know about):
```python
camera_config = {"top": OpenCVCameraConfig(index_or_path="/dev/video2", ...),
                 "wrist": OpenCVCameraConfig(index_or_path="/dev/video0", ...)}
```

## Why The Current Setup Fails

1. **Robot host** only initializes cameras from `lekiwi_cameras_config()` (currently "front" and "wrist")
2. **Robot host** only sends camera data for cameras it has initialized (`lekiwi_host.py` line 103):
   ```python
   for cam_key, _ in robot.cameras.items():  # Only iterates over robot's cameras
   ```
3. **Your client** expects different camera names ("top" instead of "front")
4. **Additional cameras** you add (like "front" on `/dev/video4`) never get initialized by the robot host

## Step-by-Step Fix Instructions

### Step 1: Update Robot Host Configuration

**Edit**: `/src/lerobot/robots/lekiwi/config_lekiwi.py`

**Replace** the `lekiwi_cameras_config()` function (lines 23-31) with your desired camera setup:

```python
def lekiwi_cameras_config() -> dict[str, CameraConfig]:
    return {
        "top": OpenCVCameraConfig(
            index_or_path="/dev/video2", fps=30, width=640, height=480, rotation=Cv2Rotation.NO_ROTATION
        ),
        "wrist": OpenCVCameraConfig(
            index_or_path="/dev/video0", fps=30, width=480, height=640, rotation=Cv2Rotation.NO_ROTATION
        ),
        "front": OpenCVCameraConfig(
            index_or_path="/dev/video4", fps=30, width=640, height=480, rotation=Cv2Rotation.NO_ROTATION
        )
        # Add more cameras as needed:
        # "side": OpenCVCameraConfig(
        #     index_or_path="/dev/video6", fps=30, width=640, height=480, rotation=Cv2Rotation.NO_ROTATION
        # )
    }
```

**Important**: Adjust the `/dev/videoX` paths based on your actual USB cable placement.

### Step 2: Update Client Configuration (Optional)

**Edit**: `examples/lekiwi/teleoperate_xbox_hybrid.py`

**Replace** line 97 to match your robot host configuration:

```python
camera_config = {
    "top": OpenCVCameraConfig(index_or_path="/dev/video2", width=640, height=480, fps=FPS, rotation=Cv2Rotation.NO_ROTATION),
    "wrist": OpenCVCameraConfig(index_or_path="/dev/video0", width=640, height=480, fps=FPS, rotation=Cv2Rotation.NO_ROTATION),
    "front": OpenCVCameraConfig(index_or_path="/dev/video4", width=640, height=480, fps=FPS, rotation=Cv2Rotation.NO_ROTATION)
}
```

**OR** simply remove the camera configuration from your teleoperation script and let it use defaults:

```python
# Remove the cameras parameter entirely:
robot_config = LeKiwiClientConfig(remote_ip="192.168.8.157", id="my_lekiwi")
```

### Step 3: Fix Syntax Error

**Edit**: `examples/lekiwi/teleoperate_xbox_hybrid.py`

**Fix** line 97 - add quotes around device paths:

```python
# BROKEN (missing quotes):
index_or_path=/dev/video2

# FIXED (with quotes):
index_or_path="/dev/video2"
```

## Testing Your Fix

### Step 1: Restart Robot Host
After changing `config_lekiwi.py`, restart the robot host:

```bash
python -m lerobot.robots.lekiwi.lekiwi_host \
    --robot.id=my_awesome_kiwi \
    --robot.use_dual_boards=true \
    --host.connection_time_s=600
```

### Step 2: Run Teleoperation
```bash
python examples/lekiwi/teleoperate_xbox_hybrid.py
```

### Step 3: Verify Camera Output
You should now see all cameras you defined in the visual output.

## USB Device Detection

To find your actual USB camera devices:

```bash
# List video devices
ls /dev/video*

# Check USB devices
lsusb | grep -i camera
```

## Key Points

1. **Both robot host AND client** must have matching camera configurations
2. **Robot host configuration** is the authoritative source - it controls which cameras actually get initialized
3. **Camera names** must match exactly between host and client
4. **Device paths** (`/dev/videoX`) depend on your physical USB connections
5. **The robot host must be restarted** after changing `config_lekiwi.py`

## Is This The Only Place?

**Yes**, `config_lekiwi.py` is the **only place** where the robot host's camera configuration is defined. The camera filtering chain is:

1. `config_lekiwi.py` → defines available cameras
2. `lekiwi.py` line 119 → creates cameras from config
3. `lekiwi_host.py` lines 103-111 → only sends data for initialized cameras
4. `lekiwi_client.py` lines 211-217 → filters incoming data (but this works correctly)

## Alternative: Environment-Based Configuration

For more flexibility, you could modify `lekiwi_cameras_config()` to read from environment variables:

```python
import os

def lekiwi_cameras_config() -> dict[str, CameraConfig]:
    # Allow environment override
    video_top = os.getenv("LEKIWI_CAMERA_TOP", "/dev/video2")
    video_wrist = os.getenv("LEKIWI_CAMERA_WRIST", "/dev/video0")
    video_front = os.getenv("LEKIWI_CAMERA_FRONT", "/dev/video4")

    return {
        "top": OpenCVCameraConfig(index_or_path=video_top, fps=30, width=640, height=480, rotation=Cv2Rotation.NO_ROTATION),
        "wrist": OpenCVCameraConfig(index_or_path=video_wrist, fps=30, width=480, height=640, rotation=Cv2Rotation.NO_ROTATION),
        "front": OpenCVCameraConfig(index_or_path=video_front, fps=30, width=640, height=480, rotation=Cv2Rotation.NO_ROTATION)
    }
```

Then set environment variables before starting the robot host:
```bash
export LEKIWI_CAMERA_TOP="/dev/video4"
export LEKIWI_CAMERA_FRONT="/dev/video6"
python -m lerobot.robots.lekiwi.lekiwi_host ...
```