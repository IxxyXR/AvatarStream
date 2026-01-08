import cv2
import mediapipe as mp
import socket
import json
import time
import threading
import struct
import numpy as np

# UDP settings
UDP_IP = "127.0.0.1"
UDP_PORT = 5005
VIRTUAL_CAM_PORT = 5006

# MediaPipe setup
mp_holistic = mp.solutions.holistic
holistic = mp_holistic.Holistic(min_detection_confidence=0.5, min_tracking_confidence=0.5)
mp_drawing = mp.solutions.drawing_utils

def virtual_camera_loop():
    try:
        import pyvirtualcam
    except ImportError:
        print("pyvirtualcam not installed. Virtual Camera disabled.")
        return

    # TCP Server
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind(("127.0.0.1", VIRTUAL_CAM_PORT))
    server_sock.listen(1)
    server_sock.settimeout(1.0) # Check for exit signal periodically

    print(f"Virtual Camera listener started on TCP port {VIRTUAL_CAM_PORT}")

    cam = None

    try:
        while True:
            try:
                conn, addr = server_sock.accept()
                print(f"Connected by {addr}")

                with conn:
                    while True:
                        # Read size (4 bytes)
                        size_data = b''
                        while len(size_data) < 4:
                            packet = conn.recv(4 - len(size_data))
                            if not packet:
                                break
                            size_data += packet

                        if not size_data:
                            break

                        size = int.from_bytes(size_data, byteorder='little') # Godot uses little endian usually? Or big?
                        # Godot StreamPeerTCP put_32 is likely little endian on intel. But network byte order is usually big.
                        # Godot documentation says put_32 puts a 32-bit integer.
                        # Let's assume little endian for now, or check documentation.
                        # Actually StreamPeer uses big-endian by default?
                        # StreamPeer.big_endian property defaults to false.
                        # So it is little endian.

                        # Read image data
                        img_data = b''
                        while len(img_data) < size:
                            packet = conn.recv(size - len(img_data))
                            if not packet:
                                break
                            img_data += packet

                        if len(img_data) != size:
                            break

                        # Parse Raw Image Data (RGB)
                        # Assumed resolution 640x360.
                        # In a more robust implementation, width/height should be part of the protocol.
                        # For now we rely on the buffer size to infer or hardcode if needed.
                        # 640*360*3 = 691200

                        # If size matches 640x360x3, we just reshape.
                        # If it's a JPG (legacy), we detect header?
                        # Let's assume the client sends raw RGB.

                        try:
                            frame = np.frombuffer(img_data, dtype=np.uint8)

                            # Heuristic to detect if it's still JPG (starts with 0xFFD8)
                            if len(frame) > 2 and frame[0] == 0xFF and frame[1] == 0xD8:
                                frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)
                                if frame is not None:
                                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                            else:
                                # Assume 640x360 RGB
                                # If the size is different, we might fail reshaping.
                                # Let's calculate based on aspect ratio 16:9?
                                # W * H * 3 = Size. W * (9/16 W) * 3 = Size => W^2 = Size / 3 * 16 / 9
                                # For now, hardcode 640x360 as target
                                target_w, target_h = 640, 360
                                if size == target_w * target_h * 3:
                                    frame = frame.reshape((target_h, target_w, 3))
                                else:
                                    # Try to guess
                                    # If not 640x360, maybe square?
                                    side = int(np.sqrt(size / 3))
                                    if side * side * 3 == size:
                                         frame = frame.reshape((side, side, 3))
                                    else:
                                         # Fallback or error
                                         continue

                            if frame is None:
                                continue

                            h, w, c = frame.shape

                        except Exception as e:
                            print(f"Frame decode error: {e}")
                            continue

                        if cam is None:
                            cam = pyvirtualcam.Camera(width=w, height=h, fps=30)
                            print(f"Virtual Camera started: {w}x{h} @ {cam.fps}fps")

                        cam.send(frame)
                        cam.sleep_until_next_frame()

            except socket.timeout:
                continue
            except Exception as e:
                print(f"Virtual Camera Connection Error: {e}")

    except KeyboardInterrupt:
        pass
    finally:
        if cam:
            cam.close()
        server_sock.close()
        print("Virtual Camera listener stopped.")

def main():
    # Start Virtual Camera thread
    vc_thread = threading.Thread(target=virtual_camera_loop, daemon=True)
    vc_thread.start()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Error: Could not open webcam.")
        return

    try:
        while cap.isOpened():
            success, image = cap.read()
            if not success:
                print("Ignoring empty camera frame.")
                continue

            # Flip the image horizontally for a later selfie-view display, and convert
            # the BGR image to RGB.
            image = cv2.cvtColor(cv2.flip(image, 1), cv2.COLOR_BGR2RGB)
            # To improve performance, optionally mark the image as not writeable to
            # pass by reference.
            image.flags.setflags(write=False)
            results = holistic.process(image)

            if results.pose_landmarks:
                # Pack data into binary format: 33 landmarks * 4 floats (x,y,z,vis)
                # 33 * 4 = 132 floats
                flattened = []
                for landmark in results.pose_landmarks.landmark:
                    flattened.extend([landmark.x, landmark.y, landmark.z, landmark.visibility])

                # 'f' is 4-byte float. 132 of them.
                # struct.pack expects args, so we use *flattened
                if len(flattened) == 33 * 4:
                    message = struct.pack(f'{len(flattened)}f', *flattened)
                    sock.sendto(message, (UDP_IP, UDP_PORT))

            # A small delay to prevent overwhelming the network and CPU
            time.sleep(0.01)

    except KeyboardInterrupt:
        pass
    finally:
        print("Closing resources.")
        holistic.close()
        cap.release()
        sock.close()

if __name__ == "__main__":
    main()
