# Testing and Verification Guide

This project includes Python scripts for pose tracking and avatar generation, Godot scenes for rendering, and a C++ GDExtension for macOS virtual camera integration.

## Automated Tests (Python)

The Python components have automated unit tests using `pytest`.

### Prerequisites

Ensure you have the Python dependencies installed:

```bash
pip install -r game/AvatarStream/scripts/python/requirements.txt
pip install pytest pytest-mock
```

### Running Tests

To run the Python unit tests, execute the following command from the root directory:

```bash
pytest game/AvatarStream/scripts/python/tests/
```

This will run tests for:
*   `holistic_tracker.py`: Verifies argument parsing, frame processing logic, and UDP packet generation.
*   `generate_avatar.py`: Verifies GLTF file creation and progress reporting.

## Manual Verification

Since the Godot environment and custom C++ GDExtensions cannot be fully tested in a headless CI/CD environment without specific setup, manual verification is required.

### Godot Project

1.  **Open Project**: Open the `game/project.godot` file in the Godot Editor (version 4.x).
2.  **Run Main Scene**: Run the `MainScene.tscn`.
3.  **Verify Tracking**:
    *   Ensure a webcam is connected.
    *   Run the Python tracker: `python game/AvatarStream/scripts/python/holistic_tracker.py`
    *   Verify that the avatar in the Godot window moves according to your movements.
4.  **Verify UI**: Check that the "Start Tracking" and "Stop Tracking" buttons work as expected.

### C++ GDExtension (macOS Virtual Camera)

1.  **Build**: Ensure the GDExtension is built for your platform.
    *   Navigate to `gdextension_cmio/`.
    *   Run `scons platform=macos`.
2.  **Verify Integration**:
    *   Launch the Godot project on macOS.
    *   Check if the "AvatarStream Camera" appears in other applications (e.g., Zoom, OBS) when the project is running.
    *   Verify that the rendered avatar is streamed to the virtual camera.

## Troubleshooting

*   **UDP Issues**: If the avatar doesn't move, check if the firewall is blocking UDP port 5005.
*   **Camera Access**: Ensure the terminal or Godot editor has permission to access the camera.
