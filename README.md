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

## Pose Listener Mode (No Godot)

To run tracking with camera selection and local HTTP JSON output:

* Windows:
  ```bat
  pickcam.bat
  ```
* Linux:
  ```bash
  ./pickcam.sh
  ```
* macOS (Terminal):
  ```bash
  ./pickcam.sh
  ```
* macOS (Finder double-click):
  ```text
  pickcam_mac.command
  ```

This starts the local listener at `127.0.0.1:40094` with:

* Pose endpoint: `http://127.0.0.1:40094/pose`
* Health endpoint: `http://127.0.0.1:40094/health`
* Built-in viewer: `http://127.0.0.1:40094/viewer`

Listener logs are written to:

* `logs/holistic_tracker.log`

## Development

*   **Python Scripts**: Located in `game/AvatarStream/scripts/python/`.
*   **Godot Project**: Located in `game/AvatarStream/`.
*   **Pose API Contract**: See [POSE_API.md](POSE_API.md) for the local HTTP listener JSON schema.
*   **Browser Pose Viewer**: `game/AvatarStream/scripts/python/web/pose_viewer.html` (also served at `/viewer` by the listener).
*   **Communication**:
    *   Python -> Godot: UDP Port 5005 (Pose Data, JSON)
    *   Godot -> Python: UDP Port 5006 (Video Frames, MJPEG)

## Mobile Support

If you export this project to Android or iOS, the Virtual Camera streaming feature is automatically disabled, and it functions as a standalone "Magic Mirror" application.

## Support My Projects

If you find this repository helpful and would like to support its development, consider making a donation:

### GitHub Sponsors
[![Sponsor](https://img.shields.io/badge/Sponsor-%23EA4AAA?style=for-the-badge&logo=github)](https://github.com/sponsors/toxicoder)

### Buy Me a Coffee
<a href="https://www.buymeacoffee.com/toxicoder" target="_blank">
    <img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" height="41" width="174">
</a>

### PayPal
[![PayPal](https://www.paypalobjects.com/en_US/i/btn/btn_donateCC_LG.gif)](https://www.paypal.com/donate/?hosted_button_id=LSHNL8YLSU3W6)

### Ko-fi
<a href="https://ko-fi.com/toxicoder" target="_blank">
    <img src="https://storage.ko-fi.com/cdn/kofi3.png" alt="Ko-fi" height="41" width="174">
</a>

### Coinbase
[![Donate via Coinbase](https://img.shields.io/badge/Donate%20via-Coinbase-0052FF?style=for-the-badge&logo=coinbase&logoColor=white)](https://commerce.coinbase.com/checkout/e07dc140-d9f7-4818-b999-fdb4f894bab7)

Your support helps maintain and improve this collection of development tools and templates. Thank you for contributing to open source!

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
