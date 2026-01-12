# Agent Instructions

This repository contains **AvatarStream**, a tool for vtuber avatar tracking and streaming. It combines a **Godot** frontend with a **Python** backend for holistic tracking using **MediaPipe**.

## Project Overview

*   **Frontend**: Godot 4 project located in `game/AvatarStream/`.
*   **Backend**: Python script (`holistic_tracker.py`) using MediaPipe for pose/hand/face tracking.
*   **Launcher**: `run.py` in the root directory acts as the unified entry point.
*   **Communication**:
    *   **Pose Data**: UDP port 5005 (Python -> Godot).
    *   **Video Frames**: TCP port 5006 (Godot -> Python) for virtual camera output.

## Directory Structure

*   `run.py`: Main launcher. Checks dependencies and launches both processes.
*   `game/AvatarStream/`: Godot project root.
    *   `scripts/`: GDScript logic.
        *   `MediaPipeBridge.gd`: Handles UDP reception and process management.
        *   `VirtualCameraSender.gd`: Handles TCP frame sending.
    *   `scripts/python/`: Python backend.
        *   `holistic_tracker.py`: Main tracking logic.
        *   `requirements.txt`: Python dependencies.
        *   `tests/`: Unit tests.
*   `gdextension_cmio/`: C++ GDExtension for macOS CoreMedia I/O integration (Virtual Camera).
    *   Uses SCons and CMake.
*   `.github/workflows/`: CI/CD configuration.

## Development & Environment

### Python
*   Dependencies: `opencv-python`, `mediapipe`, `pyvirtualcam`, `pytest`, `pytest-mock`, `pyinstaller`.
*   Installation: `run.py` attempts to auto-install from `game/AvatarStream/scripts/python/requirements.txt`.
*   **Note**: `run.py` sets `AVATARSTREAM_LAUNCHED_BY_RUNNER=1` to prevent Godot from trying to launch the Python script itself.

### Godot
*   Requires **Godot 4**.
*   The project uses a GDExtension (`gdextension_cmio.gdextension`) which may need to be compiled for macOS support.

## Testing

### Python Unit Tests
*   Located in `game/AvatarStream/scripts/python/tests/`.
*   Run with `pytest`.
*   **Important**: Tests mock `mediapipe`, `cv2`, and `pyvirtualcam` to allow running in headless CI environments.
*   When writing new tests, ensure you mock these external dependencies if they rely on hardware or display.

### C++ / GDExtension
*   Testing is currently manual.

## Agent Guidelines

1.  **Run Tests**: Before submitting any changes to the Python backend, you **MUST** run the unit tests:
    ```bash
    pytest game/AvatarStream/scripts/python/tests/
    ```
2.  **Dependency Management**: If you add a new Python library, add it to `game/AvatarStream/scripts/python/requirements.txt`.
3.  **Launcher Logic**: If modifying `run.py`, ensure it correctly detects the frozen state (`sys.frozen`) to support compiled builds.
4.  **Protocol Changes**: If you modify the data packet format in `holistic_tracker.py` (UDP), you must also update the parsing logic in `game/AvatarStream/scripts/MediaPipeBridge.gd` to match.
5.  **Virtual Camera**: The virtual camera implementation relies on `pyvirtualcam` in Python and a custom GDExtension on macOS. Be careful when modifying camera initialization logic.
