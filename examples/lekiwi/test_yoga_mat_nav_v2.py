#!/usr/bin/env python
"""
Navigate through doorway and stop on purple yoga mat.
Version 2: Improved color detection for violet/blue-purple mats.
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

def detect_purple_mat(image, threshold=0.03):
    """
    Detect purple/blue-purple yoga mat in image.
    Returns (detected, confidence, mask)
    
    Purple/violet in HSV: Hue ~240-280° (blue-purple to purple)
    """
    import cv2
    
    # Convert to HSV
    hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
    
    # Wider purple range to catch violet/blue-purple mats
    # Hue: 240-280 degrees (in OpenCV: 120-140 out of 180)
    # Extended to capture more blue-purple shades
    lower_purple1 = np.array([110, 30, 40])   # Blue-purple
    upper_purple1 = np.array([150, 255, 255])  # Purple
    
    # Alternative purple range (for pinker/paler purples)
    lower_purple2 = np.array([140, 20, 30])   
    upper_purple2 = np.array([170, 255, 255])  
    
    # Create masks
    mask1 = cv2.inRange(hsv, lower_purple1, upper_purple1)
    mask2 = cv2.inRange(hsv, lower_purple2, upper_purple2)
    mask = cv2.bitwise_or(mask1, mask2)
    
    # Focus on bottom half of image (floor area)
    h, w = mask.shape
    bottom_mask = mask[h//2:, :]  # Bottom half only
    
    # Calculate percentage of purple pixels in bottom half
    purple_pixels = np.sum(bottom_mask > 0)
    total_pixels = bottom_mask.size
    confidence = purple_pixels / total_pixels
    
    # Detect if significant purple area found
    detected = confidence > threshold
    
    return detected, confidence, mask

def analyze_floor_color(image):
    """Analyze the floor color to help debug."""
    import cv2
    hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
    
    # Get bottom half
    h, w = hsv.shape[:2]
    bottom = hsv[h//2:, :]
    
    # Average color
    avg_hsv = np.mean(bottom, axis=(0,1))
    
    return avg_hsv

def main():
    print("=" * 60)
    print("🧘‍♀️🚗 Yoga Mat Navigation - V2")
    print("=" * 60)
    print("\nNavigating through doorway, stopping on purple yoga mat.")
    print("Improved color detection for violet/blue-purple mats.")
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
    
    # Analyze initial floor color
    import cv2
    avg_hsv = analyze_floor_color(obs['front'])
    print(f"\n📊 Initial floor color (HSV): H={avg_hsv[0]:.1f}, S={avg_hsv[1]:.1f}, V={avg_hsv[2]:.1f}")
    
    # Save initial view
    timestamp = int(time.time())
    save_image(obs['front'], f'/tmp/yoga2_start_{timestamp}.jpg')
    
    # Check for mat at start
    detected, conf, _ = detect_purple_mat(obs['front'])
    print(f"   Purple detection: {detected} (confidence: {conf:.3f})")
    
    # Navigation parameters
    speed = 0.10  # m/s - slower for precision
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
        save_image(obs['front'], f'/tmp/yoga2_p1_{img_counter}.jpg')
        detected, conf, _ = detect_purple_mat(obs['front'])
        avg_hsv = analyze_floor_color(obs['front'])
        print(f"   📸 Rotated - Purple: {detected} ({conf:.3f}) | Floor H={avg_hsv[0]:.1f}")
    
    # Phase 2: Move through doorway while scanning for mat
    print("\n🚪 Phase 2: Moving through doorway, scanning for yoga mat...")
    print("   (Continuously monitoring floor color)")
    
    # Start moving forward
    agent.move_base(speed, 0, 0, duration=10.0)  # Max 10 seconds
    
    start_time = time.time()
    last_save = 0
    save_interval = 0.5
    
    while time.time() - start_time < 10.0 and not mat_detected:
        obs = agent.get_observation()
        elapsed = time.time() - start_time
        
        if obs:
            # Check for purple mat
            detected, confidence, mask = detect_purple_mat(obs['front'])
            
            # Save periodic frames with detection info
            if elapsed - last_save > save_interval:
                img_counter += 1
                save_image(obs['front'], f'/tmp/yoga2_search_{img_counter:02d}.jpg')
                avg_hsv = analyze_floor_color(obs['front'])
                print(f"   📸 t={elapsed:.1f}s - Purple: {detected} ({confidence:.3f}) | H={avg_hsv[0]:.0f}")
                last_save = elapsed
            
            # Check if we're on the mat (lower threshold since we confirmed mat is there)
            if detected and confidence > 0.04:
                print(f"\n   🎯 YOGA MAT DETECTED! Confidence: {confidence:.3f}")
                print(f"   🛑 Stopping robot...")
                agent.stop_base()
                mat_detected = True
                
                # Save detection frame
                img_counter += 1
                save_image(obs['front'], f'/tmp/yoga2_detected_{img_counter:02d}.jpg')
                break
        
        time.sleep(0.05)
    
    if not mat_detected:
        print("\n   ⚠️  Max distance reached without detecting mat")
        print("   💡 Checking current position...")
        obs = agent.get_observation()
        if obs:
            detected, conf, _ = detect_purple_mat(obs['front'])
            if detected:
                print(f"   ✅ Actually ON mat now! Confidence: {conf:.3f}")
                mat_detected = True
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
        save_image(obs['front'], f'/tmp/yoga2_final_{int(time.time())}.jpg')
        detected, conf, _ = detect_purple_mat(obs['front'])
        avg_hsv = analyze_floor_color(obs['front'])
        print(f"\n📊 Final detection: {detected} (confidence: {conf:.3f})")
        print(f"   Floor color HSV: H={avg_hsv[0]:.1f}, S={avg_hsv[1]:.1f}, V={avg_hsv[2]:.1f}")
    
    print(f"\n📁 Saved {img_counter} navigation frames to /tmp/")
    
    # Cleanup
    loop.stop()
    print("\n✓ Robot disconnected")

if __name__ == "__main__":
    main()
