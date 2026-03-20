#!/usr/bin/env python
"""
Navigate through doorway and stop on purple yoga mat.
Uses color detection to identify the mat.
"""

import sys
import time
import numpy as np
sys.path.insert(0, '/home/darren/lerobot/examples/lekiwi')

from agent_control import LeKiwiAgentLoop, AgentInterface

def save_image(img, filename):
    """Save a numpy image to file."""
    from PIL import Image
    Image.fromarray(img).save(filename)
    return filename

def detect_purple_mat(image, threshold=0.05):
    """
    Detect purple yoga mat in image.
    Returns (detected, confidence, mask)
    
    Purple in HSV: Hue ~260-280°, Saturation high, Value medium-high
    """
    import cv2
    
    # Convert to HSV
    hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
    
    # Define purple range (yoga mats are typically bright purple)
    # Hue: 260-280 degrees (in OpenCV: 130-140 out of 180)
    lower_purple = np.array([120, 50, 50])   # Lower bound
    upper_purple = np.array([160, 255, 255])  # Upper bound
    
    # Create mask
    mask = cv2.inRange(hsv, lower_purple, upper_purple)
    
    # Calculate percentage of purple pixels
    purple_pixels = np.sum(mask > 0)
    total_pixels = mask.size
    confidence = purple_pixels / total_pixels
    
    # Detect if significant purple area found
    detected = confidence > threshold
    
    return detected, confidence, mask

def main():
    print("=" * 60)
    print("🧘‍♀️🚗 Yoga Mat Navigation Mission")
    print("=" * 60)
    print("\nNavigating through doorway, stopping on purple yoga mat.")
    print("-" * 60)
    
    # Initialize
    print("\n📡 Connecting to robot...")
    loop = LeKiwiAgentLoop(robot_ip="localhost", fps=30, enable_visualization=False)
    loop.start()
    agent = AgentInterface(loop.agent_teleop)
    print("✓ Connected")
    
    # Wait for camera feed
    print("\n⏳ Waiting for camera feed...")
    for _ in range(20):
        obs = agent.get_observation()
        if obs is not None and 'front' in obs:
            break
        time.sleep(0.1)
    
    if obs is None or 'front' not in obs:
        print("❌ Failed to get camera feed")
        loop.stop()
        return
    
    print("✓ Cameras active")
    
    # Save initial view
    timestamp = int(time.time())
    save_image(obs['front'], f'/tmp/yoga_start_{timestamp}.jpg')
    print(f"\n📸 Saved initial view")
    
    # Check for mat at start
    detected, conf, _ = detect_purple_mat(obs['front'])
    print(f"   Purple detection: {detected} (confidence: {conf:.3f})")
    
    # Navigation parameters
    speed = 0.12  # m/s - slower for precision
    rot_speed = 25  # deg/s
    
    print("\n" + "=" * 60)
    print("🎬 Starting yoga mat navigation")
    print("=" * 60)
    
    img_counter = 0
    mat_detected = False
    
    # Phase 1: Rotate left to face the door
    print("\n🔄 Phase 1: Rotating to face doorway...")
    agent.move_base(0, 0, rot_speed, duration=2.0)
    time.sleep(2.5)
    
    img_counter += 1
    obs = agent.get_observation()
    if obs:
        save_image(obs['front'], f'/tmp/yoga_p1_{img_counter}.jpg')
        detected, conf, _ = detect_purple_mat(obs['front'])
        print(f"   📸 Rotated - Purple: {detected} ({conf:.3f})")
    
    # Phase 2: Move through doorway while scanning for mat
    print("\n🚪 Phase 2: Moving through doorway, scanning for yoga mat...")
    
    # Start moving forward
    agent.move_base(speed, 0, 0, duration=8.0)  # Max 8 seconds
    
    start_time = time.time()
    last_save = 0
    save_interval = 0.8
    
    while time.time() - start_time < 8.0 and not mat_detected:
        obs = agent.get_observation()
        elapsed = time.time() - start_time
        
        if obs:
            # Check for purple mat
            detected, confidence, mask = detect_purple_mat(obs['front'])
            
            # Save periodic frames
            if elapsed - last_save > save_interval:
                img_counter += 1
                save_image(obs['front'], f'/tmp/yoga_search_{img_counter}.jpg')
                print(f"   📸 t={elapsed:.1f}s - Purple: {detected} ({confidence:.3f})")
                last_save = elapsed
            
            # Check if we're on the mat
            if detected and confidence > 0.08:  # Threshold for "on the mat"
                print(f"\n   🎯 YOGA MAT DETECTED! Confidence: {confidence:.3f}")
                print(f"   🛑 Stopping robot...")
                agent.stop_base()
                mat_detected = True
                
                # Save detection frame
                img_counter += 1
                save_image(obs['front'], f'/tmp/yoga_detected_{img_counter}.jpg')
                break
        
        time.sleep(0.05)
    
    if not mat_detected:
        print("\n   ⚠️  Max distance reached without detecting mat")
        agent.stop_base()
    
    time.sleep(0.5)
    
    # Final position
    print("\n" + "=" * 60)
    if mat_detected:
        print("✅ SUCCESS: Robot stopped on purple yoga mat!")
    else:
        print("⚠️  Navigation ended - mat not detected")
    print("=" * 60)
    
    # Final snapshot
    obs = agent.get_observation()
    if obs:
        save_image(obs['front'], f'/tmp/yoga_final_{int(time.time())}.jpg')
        detected, conf, _ = detect_purple_mat(obs['front'])
        print(f"\n📊 Final purple detection: {detected} (confidence: {conf:.3f})")
    
    print(f"\n📁 Saved {img_counter} navigation frames to /tmp/")
    
    # Cleanup
    loop.stop()
    print("\n✓ Robot disconnected")

if __name__ == "__main__":
    main()
