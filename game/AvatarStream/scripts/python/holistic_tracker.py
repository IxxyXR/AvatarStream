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
                            print(f"Frame decode error: {e}")
                            continue

                        # Update camera if resolution changed
                        if cam is not None and (cam.width != w or cam.height != h):
                            print(f"Resolution changed from {cam.width}x{cam.height} to {w}x{h}. Restarting Virtual Camera.")
                            cam.close()
                            cam = None

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
