# AvatarStream

This project implements a virtual avatar controlled by MediaPipe Holistic tracking. The Python script tracks body pose and sends the data to Godot, which renders the avatar. The rendered view is then sent back to a virtual camera device, allowing you to use the avatar in meetings (Zoom, Teams, etc.).

## Prerequisites

### General
*   **Python 3.8+**
*   **Godot Engine 4.x** (Ensure `godot` is in your PATH, or specify the path when running)

### Python Dependencies
Install the required packages:
```bash
pip install -r game/AvatarStream/scripts/python/requirements.txt
```

### Virtual Camera Setup

#### Windows
1.  Install [OBS Studio](https://obsproject.com/).
2.  OBS Studio comes with a Virtual Camera built-in. However, `pyvirtualcam` usually works with the Unity Capture driver or similar DirectShow filters.
    *   **Recommended**: Install [OBS-VirtualCam](https://obsproject.com/forum/resources/obs-virtualcam.539/) if the built-in one isn't detected, or better yet, simply use `pyvirtualcam` which often defaults to OBS Virtual Camera if available.
    *   Alternatively, `pyvirtualcam` on Windows often uses the `unity-capture` driver.

#### Linux
1.  Install `v4l2loopback`:
    ```bash
    sudo apt install v4l2loopback-dkms
    ```
2.  Create a virtual device:
    ```bash
    sudo modprobe v4l2loopback devices=1 video_nr=20 card_label="AvatarStream" exclusive_caps=1
    ```
    (You might want to add this to `/etc/modules` or a startup script).

#### macOS
*   `pyvirtualcam` usually relies on OBS Virtual Camera on macOS as well. Ensure OBS is installed and the Virtual Camera is set up.

## Running the Project

Use the unified launcher script `run.py` at the root of the repository:

```bash
python run.py
```

This script will:
1.  Check if dependencies are installed.
2.  Start the Python tracking script in the background.
3.  Launch the Godot project.
4.  Clean up processes when you close Godot or press Ctrl+C.

**Options:**
*   `--godot-path <path>`: Specify the path to your Godot executable if it's not in your PATH.
    ```bash
    python run.py --godot-path /path/to/Godot_v4.x
    ```

## Development

*   **Python Scripts**: Located in `game/AvatarStream/scripts/python/`.
*   **Godot Project**: Located in `game/AvatarStream/`.
*   **Communication**:
    *   Python -> Godot: UDP Port 5005 (Pose Data, JSON)
    *   Godot -> Python: UDP Port 5006 (Video Frames, MJPEG)

## Mobile Support

If you export this project to Android or iOS, the Virtual Camera streaming feature is automatically disabled, and it functions as a standalone "Magic Mirror" application.
