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

def run_python_tracker(python_script_path):
    print(f"Starting Python tracker: {python_script_path}")
    try:
        subprocess.run([sys.executable, python_script_path], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Python tracker exited with error: {e}")
    except KeyboardInterrupt:
        pass

def run_godot(godot_path, project_path):
    print(f"Starting Godot: {godot_path} --path {project_path}")
    try:
        subprocess.run([godot_path, "--path", project_path], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Godot exited with error: {e}")
    except KeyboardInterrupt:
        pass

def main():
    parser = argparse.ArgumentParser(description="Unified Launcher for AvatarStream")
    parser.add_argument("--godot-path", type=str, help="Path to Godot executable", default="godot")
    args = parser.parse_args()

    os_name = get_os()
    print(f"Detected OS: {os_name}")

    if not check_dependencies():
        sys.exit(1)

    python_script = os.path.join("game", "AvatarStream", "scripts", "python", "holistic_tracker.py")
    project_path = os.path.join("game", "AvatarStream")

    if not os.path.exists(python_script):
        print(f"Error: Python script not found at {python_script}")
        sys.exit(1)

    # Launch Python tracker in a separate thread/process
    # We use a thread for simplicity here, but in a real scenario, separate processes are better managed.
    # However, since we want to kill both, let's use subprocess.Popen and manage them.

    tracker_process = subprocess.Popen([sys.executable, python_script])

    # Launch Godot
    # We wait for Godot to exit, then we kill the tracker.
    godot_process = None

    # Set environment variable to tell Godot it's launched by the runner
    env = os.environ.copy()
    env["AVATARSTREAM_LAUNCHED_BY_RUNNER"] = "1"

    try:
        godot_process = subprocess.Popen([args.godot_path, "--path", project_path], env=env)
        godot_process.wait()
    except FileNotFoundError:
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
