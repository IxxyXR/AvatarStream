import cv2
import mediapipe as mp
import socket
import json
import time
import threading
import numpy as np
import argparse
import platform
import logging
import os
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# UDP settings
UDP_IP = "127.0.0.1"
UDP_PORT = 5005
VIRTUAL_CAM_PORT = 5006
DEFAULT_LOG_FILE = os.path.join("logs", "holistic_tracker.log")
DEFAULT_HTTP_URL = "http://127.0.0.1:40094/pose"
DEFAULT_VIEWER_FILE = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "web", "pose_viewer.html")
)
logger = logging.getLogger("holistic_tracker")

POSE_LANDMARK_NAMES = [
    "nose",
    "left_eye_inner",
    "left_eye",
    "left_eye_outer",
    "right_eye_inner",
    "right_eye",
    "right_eye_outer",
    "left_ear",
    "right_ear",
    "mouth_left",
    "mouth_right",
    "left_shoulder",
    "right_shoulder",
    "left_elbow",
    "right_elbow",
    "left_wrist",
    "right_wrist",
    "left_pinky",
    "right_pinky",
    "left_index",
    "right_index",
    "left_thumb",
    "right_thumb",
    "left_hip",
    "right_hip",
    "left_knee",
    "right_knee",
    "left_ankle",
    "right_ankle",
    "left_heel",
    "right_heel",
    "left_foot_index",
    "right_foot_index",
]

POSE_SEGMENTS = {
    "left_upper_arm": ("left_shoulder", "left_elbow"),
    "right_upper_arm": ("right_shoulder", "right_elbow"),
    "left_forearm": ("left_elbow", "left_wrist"),
    "right_forearm": ("right_elbow", "right_wrist"),
    "left_thigh": ("left_hip", "left_knee"),
    "right_thigh": ("right_hip", "right_knee"),
    "left_calf": ("left_knee", "left_ankle"),
    "right_calf": ("right_knee", "right_ankle"),
    "left_torso": ("left_shoulder", "left_hip"),
    "right_torso": ("right_shoulder", "right_hip"),
    "shoulder_line": ("left_shoulder", "right_shoulder"),
    "hip_line": ("left_hip", "right_hip"),
}


class PoseState:
    def __init__(self):
        self._lock = threading.Lock()
        self._payload = None
        self._updated_ms = None

    def set_payload(self, payload):
        with self._lock:
            self._payload = payload
            self._updated_ms = int(time.time() * 1000)

    def get_snapshot(self):
        with self._lock:
            return self._payload, self._updated_ms


def setup_logging(log_file):
    log_dir = os.path.dirname(log_file)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)

    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    logger.propagate = False

def virtual_camera_loop():
    try:
        import pyvirtualcam
    except ImportError:
        logger.warning("pyvirtualcam not installed. Virtual Camera disabled.")
        return

    # TCP Server
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind(("127.0.0.1", VIRTUAL_CAM_PORT))
    server_sock.listen(1)
    server_sock.settimeout(1.0) # Check for exit signal periodically

    logger.info("Virtual Camera listener started on TCP port %s", VIRTUAL_CAM_PORT)

    cam = None

    try:
        while True:
            try:
                conn, addr = server_sock.accept()
                logger.info("Connected by %s", addr)

                with conn:
                    while True:
                        # Read width (4 bytes) and height (4 bytes)
                        header_data = b''
                        while len(header_data) < 8:
                            packet = conn.recv(8 - len(header_data))
                            if not packet:
                                break
                            header_data += packet

                        if not header_data:
                            break

                        width = int.from_bytes(header_data[0:4], byteorder='little')
                        height = int.from_bytes(header_data[4:8], byteorder='little')

                        size = width * height * 3

                        # Read image data
                        img_data = b''
                        while len(img_data) < size:
                            packet = conn.recv(size - len(img_data))
                            if not packet:
                                break
                            img_data += packet

                        if len(img_data) != size:
                            break

                        try:
                            frame = np.frombuffer(img_data, dtype=np.uint8)
                            frame = frame.reshape((height, width, 3))

                            h, w, c = frame.shape

                        except Exception as e:
                            logger.warning("Frame decode error: %s", e)
                            continue

                        # Update camera if resolution changed
                        if cam is not None and (cam.width != w or cam.height != h):
                            logger.info(
                                "Resolution changed from %sx%s to %sx%s. Restarting Virtual Camera.",
                                cam.width,
                                cam.height,
                                w,
                                h,
                            )
                            cam.close()
                            cam = None

                        if cam is None:
                            cam = pyvirtualcam.Camera(width=w, height=h, fps=30)
                            logger.info("Virtual Camera started: %sx%s @ %sfps", w, h, cam.fps)

                        cam.send(frame)
                        cam.sleep_until_next_frame()

            except socket.timeout:
                continue
            except Exception as e:
                logger.warning("Virtual Camera Connection Error: %s", e)

    except KeyboardInterrupt:
        pass
    finally:
        if cam:
            cam.close()
        server_sock.close()
        logger.info("Virtual Camera listener stopped.")

def build_parser():
    parser = argparse.ArgumentParser(description="MediaPipe holistic tracker for AvatarStream")
    parser.add_argument("--debug", action="store_true", help="Print periodic pose debug output to console")
    parser.add_argument("--debug-interval", type=float, default=1.0, help="Seconds between debug prints")
    parser.add_argument("--no-virtual-cam", action="store_true", help="Disable virtual camera TCP listener thread")
    parser.add_argument("--camera-index", type=int, default=None, help="OpenCV camera index to use")
    parser.add_argument("--list-cameras", action="store_true", help="List available cameras and exit")
    parser.add_argument("--select-camera", action="store_true", help="Interactively select camera index from a list, then start")
    parser.add_argument("--pick-camera", action="store_true", help="Alias for --select-camera")
    parser.add_argument("--log-file", default=DEFAULT_LOG_FILE, help="Path to log file")
    parser.add_argument("--transport", choices=["http", "udp", "none"], default="http", help="Pose output transport")
    parser.add_argument("--http-url", default=DEFAULT_HTTP_URL, help="HTTP endpoint URL")
    parser.add_argument("--http-method", choices=["get", "post"], default="get", help="HTTP method for pose upload")
    parser.add_argument("--http-query-param", default="data", help="Query parameter name used for JSON payload in GET mode")
    parser.add_argument("--http-timeout", type=float, default=0.2, help="HTTP timeout in seconds")
    parser.add_argument("--listen-http", action="store_true", help="Run local HTTP listener that serves latest pose JSON")
    parser.add_argument("--listen-host", default="127.0.0.1", help="Listener host for local HTTP server")
    parser.add_argument("--listen-port", type=int, default=40094, help="Listener port for local HTTP server")
    parser.add_argument("--listen-path", default="/pose", help="Listener endpoint path for pose JSON")
    return parser


def list_available_cameras(max_probe=10):
    cameras = []
    os_name = platform.system()
    indexed_names = []

    if os_name == "Windows":
        try:
            from pygrabber.dshow_graph import FilterGraph
            indexed_names = list(enumerate(FilterGraph().get_input_devices()))
        except Exception:
            indexed_names = []

    if indexed_names:
        for idx, name in indexed_names:
            opened = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
            available = opened.isOpened()
            if opened.isOpened():
                opened.release()

            # Some cameras fail CAP_DSHOW probe but still open with default backend.
            if not available:
                fallback = cv2.VideoCapture(idx)
                available = fallback.isOpened()
                if fallback.isOpened():
                    fallback.release()

            cameras.append({"index": idx, "name": name, "available": available})
        return cameras

    # Fallback when names are unavailable: probe numeric indices.
    for idx in range(max_probe):
        opened = cv2.VideoCapture(idx)
        available = opened.isOpened()
        if available:
            opened.release()
            cameras.append({"index": idx, "name": f"Camera {idx}", "available": True})
    return cameras


def choose_camera_index(cameras):
    if not cameras:
        print("No cameras were detected.")
        return None

    print("Detected cameras:")
    for cam in cameras:
        status = "opens" if cam["available"] else "probe-failed (may still work)"
        print(f'  [{cam["index"]}] {cam["name"]} ({status})')

    while True:
        print("Choose camera index and press Enter: ", end="", flush=True)
        try:
            raw = input().strip()
        except EOFError:
            print("\nInput stream unavailable; cannot prompt for camera selection.")
            return None
        try:
            choice = int(raw)
        except ValueError:
            print("Please enter a valid integer index.")
            continue

        if any(cam["index"] == choice for cam in cameras):
            return choice
        print("Index not in detected camera list.")


def open_selected_camera(camera_index):
    attempts = []
    if platform.system() == "Windows":
        attempts = [
            ("CAP_DSHOW", lambda: cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)),
            ("CAP_MSMF", lambda: cv2.VideoCapture(camera_index, cv2.CAP_MSMF)),
            ("DEFAULT", lambda: cv2.VideoCapture(camera_index)),
        ]
    else:
        attempts = [("DEFAULT", lambda: cv2.VideoCapture(camera_index))]

    for backend_name, opener in attempts:
        cap = opener()
        if cap.isOpened():
            logger.info("Opened camera index %s using %s backend.", camera_index, backend_name)
            return cap, backend_name
        logger.warning("Open failed for camera index %s using %s backend.", camera_index, backend_name)
        cap.release()

    return None, None


def _round6(value):
    return round(float(value), 6)


def build_pose_payload(results):
    named_landmarks = {}
    for idx, landmark in enumerate(results.pose_landmarks.landmark):
        if idx >= len(POSE_LANDMARK_NAMES):
            continue
        name = POSE_LANDMARK_NAMES[idx]
        named_landmarks[name] = {
            "x": _round6(landmark.x),
            "y": _round6(landmark.y),
            "z": _round6(landmark.z),
            "visibility": _round6(landmark.visibility),
        }

    segments = {}
    for segment_name, (start_name, end_name) in POSE_SEGMENTS.items():
        start = named_landmarks.get(start_name)
        end = named_landmarks.get(end_name)
        if start is None or end is None:
            continue
        segments[segment_name] = {
            "start": start_name,
            "end": end_name,
            "start_point": start,
            "end_point": end,
        }

    return {
        "timestamp_ms": int(time.time() * 1000),
        "landmarks": named_landmarks,
        "segments": segments,
    }


def send_http_pose(payload, args):
    payload_json = json.dumps(payload, separators=(",", ":"))
    method = args.http_method.lower()

    if method == "get":
        parts = urllib.parse.urlsplit(args.http_url)
        existing_query = urllib.parse.parse_qsl(parts.query, keep_blank_values=True)
        existing_query.append((args.http_query_param, payload_json))
        new_query = urllib.parse.urlencode(existing_query)
        url = urllib.parse.urlunsplit((parts.scheme, parts.netloc, parts.path, new_query, parts.fragment))
        request = urllib.request.Request(url=url, method="GET")
        with urllib.request.urlopen(request, timeout=args.http_timeout):
            return

    data = payload_json.encode("utf-8")
    request = urllib.request.Request(
        url=args.http_url,
        data=data,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=args.http_timeout):
        return


def send_udp_pose(payload, sock):
    message = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    sock.sendto(message, (UDP_IP, UDP_PORT))


def start_pose_http_listener(args, pose_state):
    listen_path = args.listen_path if args.listen_path.startswith("/") else f"/{args.listen_path}"

    class PoseHandler(BaseHTTPRequestHandler):
        def do_OPTIONS(self):
            self.send_response(204)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.end_headers()

        def do_GET(self):
            parsed = urllib.parse.urlsplit(self.path)
            if parsed.path == "/health":
                self._write_json(200, {"ok": True, "service": "holistic_tracker"})
                return
            if parsed.path == "/viewer" or parsed.path == "/viewer.html":
                if os.path.exists(DEFAULT_VIEWER_FILE):
                    with open(DEFAULT_VIEWER_FILE, "rb") as f:
                        html = f.read()
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.send_header("Content-Length", str(len(html)))
                    self.end_headers()
                    self.wfile.write(html)
                else:
                    self._write_json(404, {"error": "Viewer file not found", "path": DEFAULT_VIEWER_FILE})
                return

            if parsed.path != listen_path:
                self._write_json(404, {"error": "Not Found", "path": parsed.path})
                return

            payload, updated_ms = pose_state.get_snapshot()
            if payload is None:
                self._write_json(503, {"error": "No pose data yet"})
                return

            self._write_json(
                200,
                {
                    "ok": True,
                    "updated_ms": updated_ms,
                    "pose": payload,
                },
            )

        def log_message(self, fmt, *values):
            logger.info("HTTP listener: " + fmt, *values)

        def _write_json(self, status_code, body):
            blob = json.dumps(body, separators=(",", ":")).encode("utf-8")
            self.send_response(status_code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Length", str(len(blob)))
            self.end_headers()
            self.wfile.write(blob)

    server = ThreadingHTTPServer((args.listen_host, args.listen_port), PoseHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    logger.info("HTTP listener started on http://%s:%s%s", args.listen_host, args.listen_port, listen_path)
    return server


def main():
    args = build_parser().parse_args()
    setup_logging(args.log_file)
    logger.info("Logging to %s", os.path.abspath(args.log_file))
    cameras = list_available_cameras()
    pose_state = PoseState()
    pose_server = None

    if args.list_cameras:
        if not cameras:
            logger.info("No cameras were detected.")
            return
        logger.info("Detected cameras:")
        for cam in cameras:
            status = "opens" if cam["available"] else "probe-failed (may still work)"
            logger.info("  [%s] %s (%s)", cam["index"], cam["name"], status)
        return

    camera_index = args.camera_index if args.camera_index is not None else 0
    if args.select_camera or args.pick_camera:
        selected = choose_camera_index(cameras)
        if selected is None:
            return
        camera_index = selected

    if args.listen_http:
        pose_server = start_pose_http_listener(args, pose_state)

    # Start Virtual Camera thread unless explicitly disabled for tracker-only debugging.
    if not args.no_virtual_cam:
        vc_thread = threading.Thread(target=virtual_camera_loop, daemon=True)
        vc_thread.start()

    mp_holistic = mp.solutions.holistic
    holistic = mp_holistic.Holistic(min_detection_confidence=0.5, min_tracking_confidence=0.5)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) if args.transport == "udp" else None
    cap, backend_name = open_selected_camera(camera_index)

    if cap is None:
        logger.error("Could not open webcam at index %s with any backend.", camera_index)
        return

    frames = 0
    last_debug_time = time.time()
    if args.transport == "http":
        logger.info(
            "Tracking started using camera index %s (%s), transport=http method=%s url=%s",
            camera_index,
            backend_name,
            args.http_method.upper(),
            args.http_url,
        )
    elif args.transport == "udp":
        logger.info("Tracking started using camera index %s (%s), transport=udp %s:%s", camera_index, backend_name, UDP_IP, UDP_PORT)
    else:
        logger.info("Tracking started using camera index %s (%s), transport=none", camera_index, backend_name)

    try:
        while cap.isOpened():
            success, image = cap.read()
            if not success:
                logger.warning("Ignoring empty camera frame.")
                continue

            # Flip the image horizontally for a later selfie-view display, and convert
            # the BGR image to RGB.
            image = cv2.cvtColor(cv2.flip(image, 1), cv2.COLOR_BGR2RGB)
            # To improve performance, optionally mark the image as not writeable to
            # pass by reference.
            image.flags.writeable = False
            results = holistic.process(image)

            if results.pose_landmarks:
                payload = build_pose_payload(results)
                pose_state.set_payload(payload)
                if args.transport != "none":
                    try:
                        if args.transport == "http":
                            send_http_pose(payload, args)
                        else:
                            send_udp_pose(payload, sock)
                    except Exception as e:
                        logger.warning("Pose send failed: %s", e)

                if args.debug:
                    now = time.time()
                    if now - last_debug_time >= max(0.1, args.debug_interval):
                        # Landmark 0 is nose in MediaPipe pose topology.
                        nose = payload["landmarks"]["nose"]
                        fps = frames / (now - last_debug_time) if now > last_debug_time else 0.0
                        print(
                            f"[debug] fps={fps:.1f} landmarks=33 "
                            f"nose=(x={nose['x']:.3f}, y={nose['y']:.3f}, z={nose['z']:.3f}, vis={nose['visibility']:.3f})"
                        )
                        logger.info(
                            "[debug] fps=%.1f landmarks=33 nose=(x=%.3f, y=%.3f, z=%.3f, vis=%.3f)",
                            fps,
                            nose["x"],
                            nose["y"],
                            nose["z"],
                            nose["visibility"],
                        )
                        frames = 0
                        last_debug_time = now

            # A small delay to prevent overwhelming the network and CPU
            time.sleep(0.01)
            frames += 1

    except KeyboardInterrupt:
        logger.info("Interrupted by user.")
    except Exception:
        logger.exception("Fatal tracker error")
        raise
    finally:
        logger.info("Closing resources.")
        holistic.close()
        cap.release()
        if sock is not None:
            sock.close()
        if pose_server is not None:
            pose_server.shutdown()
            pose_server.server_close()
            logger.info("HTTP listener stopped.")

if __name__ == "__main__":
    main()
