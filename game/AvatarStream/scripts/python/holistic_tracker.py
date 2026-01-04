import cv2
import mediapipe as mp
import socket
import json
import time
import argparse
import signal
import sys
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Global flag for the main loop
running = True

def signal_handler(sig, frame):
    global running
    logging.info("Received signal to stop.")
    running = False

def main():
    global running

    # Argument parsing
    parser = argparse.ArgumentParser(description='Holistic Tracker for AvatarStream')
    parser.add_argument('--camera', type=int, default=0, help='Camera index')
    parser.add_argument('--ip', type=str, default="127.0.0.1", help='UDP Target IP')
    parser.add_argument('--port', type=int, default=5005, help='UDP Target Port')
    parser.add_argument('--width', type=int, default=None, help='Camera capture width')
    parser.add_argument('--height', type=int, default=None, help='Camera capture height')
    parser.add_argument('--no-mirror', action='store_true', help='Disable camera mirroring')

    args = parser.parse_args()

    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # UDP settings
    udp_ip = args.ip
    udp_port = args.port

    # MediaPipe setup
    mp_holistic = mp.solutions.holistic
    # Initialize MediaPipe Holistic with reasonable defaults
    # Ref: https://google.github.io/mediapipe/solutions/holistic.html
    holistic = mp_holistic.Holistic(
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
        model_complexity=1,
        smooth_landmarks=True
    )

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    logging.info(f"Starting holistic tracker on Camera {args.camera}")
    logging.info(f"Sending data to {udp_ip}:{udp_port}")

    cap = cv2.VideoCapture(args.camera)

    if args.width:
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, args.width)
    if args.height:
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, args.height)

    if not cap.isOpened():
        logging.error(f"Error: Could not open webcam with index {args.camera}.")
        sys.exit(1)

    logging.info("Camera opened successfully.")

    try:
        while running and cap.isOpened():
            success, image = cap.read()
            if not success:
                logging.warning("Ignoring empty camera frame.")
                time.sleep(0.1)
                continue

            # Flip the image horizontally for a later selfie-view display, and convert
            # the BGR image to RGB.
            if not args.no_mirror:
                image = cv2.flip(image, 1)

            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

            # To improve performance, optionally mark the image as not writeable to
            # pass by reference.
            image.flags.setflags(write=False)
            results = holistic.process(image)

            landmarks_data = []
            if results.pose_landmarks:
                for landmark in results.pose_landmarks.landmark:
                    landmarks_data.append({
                        'x': landmark.x,
                        'y': landmark.y,
                        'z': landmark.z,
                        'visibility': landmark.visibility,
                    })

            if landmarks_data:
                try:
                    message = json.dumps({"pose_landmarks": landmarks_data}).encode('utf-8')
                    sock.sendto(message, (udp_ip, udp_port))
                except Exception as e:
                    logging.error(f"Failed to send UDP packet: {e}")

            # A small delay to prevent overwhelming the network and CPU
            # Adjust sleep time based on desired update rate if needed
            time.sleep(0.01)

    except KeyboardInterrupt:
        logging.info("KeyboardInterrupt received.")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
    finally:
        logging.info("Closing resources.")
        holistic.close()
        cap.release()
        sock.close()
        logging.info("Resources released. Exiting.")

if __name__ == "__main__":
    main()
