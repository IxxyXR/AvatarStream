# AvatarStream Refactor TODOs

## Phase 1: Environment & Setup
- [x] Create `TODO.md`
- [x] Dependency Management:
    - [x] Analyze Python imports in `game/AvatarStream/scripts/python/holistic_tracker.py`
    - [x] Update `game/AvatarStream/scripts/python/requirements.txt` (include `opencv-python`, `mediapipe`, `pyvirtualcam`)
- [x] Unified Launcher (`run.py`):
    - [x] Create `run.py` at the root
    - [x] Detect OS (Windows/Linux/Mac)
    - [x] Verify dependencies are installed
    - [x] Launch Python tracking script in background
    - [x] Launch Godot executable (configurable via `.env` or args)
    - [x] Gracefully kill processes on exit

## Phase 2: Cross-Platform Virtual Camera
- [x] Modify Godot Project:
    - [x] Create script to capture `Viewport` texture
    - [x] Send frame data back to Python (UDP/TCP)
- [x] Update Python Script:
    - [x] Integrate `pyvirtualcam`
    - [x] Add listener thread for Godot frames
    - [x] Push frames to virtual camera

## Phase 3: Mobile & Cleanup
- [x] Mobile Logic:
    - [x] Add `OS.get_name()` check in Godot
    - [x] Disable frame-sending logic on Android/iOS
- [x] Documentation:
    - [x] Update `README.md` with `run.py` instructions
    - [x] Add setup notes for Windows (OBS) and Linux (v4l2loopback)

## Phase 4: Optimization & UX (Current)
- [x] **Performance**:
    - [x] Switch Pose Data from JSON to Binary (UDP) in `holistic_tracker.py` and `MediaPipeBridge.gd` (~80% size reduction)
    - [x] Switch Video Stream from MJPEG to Raw RGB (TCP) in `VirtualCameraSender.gd` and `holistic_tracker.py` (Eliminate encode/decode CPU cost)
- [x] **Setup & UX**:
    - [x] Auto-install Python dependencies in `run.py` if missing
    - [x] Fix double-launch bug: Godot no longer launches Python if `run.py` already did (via `AVATARSTREAM_LAUNCHED_BY_RUNNER` env var)
- [x] **Quality**:
    - [x] Add protocol unit tests (`game/AvatarStream/scripts/python/tests/test_protocol.py`)
