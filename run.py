import os
import sys
import platform
import subprocess
import threading
import time
import argparse
from pathlib import Path

def get_os():
    return platform.system()

def check_dependencies():
    # Skip dependency check if frozen (dependencies are bundled)
    if getattr(sys, 'frozen', False):
        return True

    print("Checking dependencies...")
    try:
        import cv2
        import mediapipe
        import pyvirtualcam
        print("Dependencies are installed.")
        return True
    except ImportError as e:
        print(f"Missing dependency: {e.name}")
        print("Attempting to install dependencies...")
        try:
            requirements_path = os.path.join("game", "AvatarStream", "scripts", "python", "requirements.txt")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", requirements_path])
            print("Dependencies installed successfully.")
            return True
        except subprocess.CalledProcessError:
            print(f"Failed to install dependencies. Please manually run: pip install -r {requirements_path}")
            return False

def main():
    parser = argparse.ArgumentParser(description="Unified Launcher for AvatarStream")
    parser.add_argument("--godot-path", type=str, help="Path to Godot executable", default="godot")
    args = parser.parse_args()

    os_name = get_os()
    print(f"Detected OS: {os_name}")

    is_frozen = getattr(sys, 'frozen', False)

    if not check_dependencies():
        sys.exit(1)

    if is_frozen:
        # Running in frozen mode (compiled executable)
        base_dir = os.path.dirname(sys.executable)

        if os_name == "Windows":
            tracker_cmd = [os.path.join(base_dir, "holistic_tracker.exe")]
            godot_executable = os.path.join(base_dir, "AvatarStream.exe")
            godot_cmd = [godot_executable]
        elif os_name == "Darwin": # macOS
             # In macOS app bundle structure might be different, but assuming side-by-side for now
             # or inside Contents/MacOS
             tracker_cmd = [os.path.join(base_dir, "holistic_tracker")]
             # If we are inside an App bundle, finding the Godot app might be different
             # But for simplicity, let's assume flat structure or adjust during build
             godot_executable = os.path.join(base_dir, "AvatarStream.app", "Contents", "MacOS", "AvatarStream")
             if not os.path.exists(godot_executable):
                 # Fallback for side-by-side non-app
                 godot_executable = os.path.join(base_dir, "AvatarStream")
             godot_cmd = [godot_executable]
        else: # Linux
            tracker_cmd = [os.path.join(base_dir, "holistic_tracker")]
            godot_executable = os.path.join(base_dir, "AvatarStream.x86_64")
            godot_cmd = [godot_executable]

    else:
        # Running in development mode
        python_script = os.path.join("game", "AvatarStream", "scripts", "python", "holistic_tracker.py")
        project_path = os.path.join("game", "AvatarStream")

        if not os.path.exists(python_script):
            print(f"Error: Python script not found at {python_script}")
            sys.exit(1)

        tracker_cmd = [sys.executable, python_script]
        godot_cmd = [args.godot_path, "--path", project_path]

    # Launch Python tracker
    print(f"Starting Python tracker: {tracker_cmd}")
    try:
        tracker_process = subprocess.Popen(tracker_cmd)
    except FileNotFoundError:
        print(f"Error: Tracker executable not found: {tracker_cmd}")
        sys.exit(1)

    # Launch Godot
    # Set environment variable to tell Godot it's launched by the runner
    env = os.environ.copy()
    env["AVATARSTREAM_LAUNCHED_BY_RUNNER"] = "1"

    print(f"Starting Godot: {godot_cmd}")
    godot_process = None
    try:
        godot_process = subprocess.Popen(godot_cmd, env=env)
        godot_process.wait()
    except FileNotFoundError:
        if is_frozen:
             print(f"Error: Godot executable not found at '{godot_cmd[0]}'.")
        else:
             print(f"Error: Godot executable not found at '{args.godot_path}'. Please provide the correct path using --godot-path.")
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        print("Stopping Python tracker...")
        tracker_process.terminate()
        tracker_process.wait()
        if godot_process and godot_process.poll() is None:
             godot_process.terminate()

if __name__ == "__main__":
    main()
