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

class HolisticTracker:
    def __init__(self, camera_idx=0, udp_ip="127.0.0.1", udp_port=5005, width=None, height=None, no_mirror=False, sock=None):
        self.camera_idx = camera_idx
        self.udp_ip = udp_ip
        self.udp_port = udp_port
        self.width = width
        self.height = height
        self.no_mirror = no_mirror
        self.running = True

        # Dependency injection for socket (useful for testing)
        if sock:
            self.sock = sock
        else:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        self.mp_holistic = mp.solutions.holistic
        self.holistic = self.mp_holistic.Holistic(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
            model_complexity=1,
            smooth_landmarks=True
        )
        self.cap = None

    def signal_handler(self, sig, frame):
        logging.info("Received signal to stop.")
        self.running = False

    def open_camera(self):
        self.cap = cv2.VideoCapture(self.camera_idx)
        if self.width:
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        if self.height:
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)

        return self.cap.isOpened()

    def process_frame(self, image):
        if self.no_mirror:
             # If no mirror is requested, we might not need to flip,
             # but standard webcam view often feels more natural flipped.
             # However, the original logic was: "if not args.no_mirror: image = cv2.flip(image, 1)"
             # So if no_mirror is False (default), we flip.
             pass
        else:
            image = cv2.flip(image, 1)

        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        # To improve performance, optionally mark the image as not writeable to
        # pass by reference.
        image_rgb.flags.writeable = False
        results = self.holistic.process(image_rgb)
        return results

    def extract_landmarks(self, results):
        landmarks_data = []
        if results.pose_landmarks:
            for landmark in results.pose_landmarks.landmark:
                landmarks_data.append({
                    'x': landmark.x,
                    'y': landmark.y,
                    'z': landmark.z,
                    'visibility': landmark.visibility,
                })
        return landmarks_data

    def send_data(self, landmarks_data):
        if landmarks_data:
            try:
                message = json.dumps({"pose_landmarks": landmarks_data}).encode('utf-8')
                self.sock.sendto(message, (self.udp_ip, self.udp_port))
                return True
            except Exception as e:
                logging.error(f"Failed to send UDP packet: {e}")
                return False
        return False

    def run(self):
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

        logging.info(f"Starting holistic tracker on Camera {self.camera_idx}")
        logging.info(f"Sending data to {self.udp_ip}:{self.udp_port}")

        if not self.open_camera():
            logging.error(f"Error: Could not open webcam with index {self.camera_idx}.")
            sys.exit(1)

        logging.info("Camera opened successfully.")

        try:
            while self.running and self.cap.isOpened():
                success, image = self.cap.read()
                if not success:
                    logging.warning("Ignoring empty camera frame.")
                    time.sleep(0.1)
                    continue

                results = self.process_frame(image)
                landmarks = self.extract_landmarks(results)
                self.send_data(landmarks)

                # A small delay to prevent overwhelming the network and CPU
                time.sleep(0.01)

        except KeyboardInterrupt:
            logging.info("KeyboardInterrupt received.")
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
        finally:
            self.close()

    def close(self):
        logging.info("Closing resources.")
        if self.holistic:
            self.holistic.close()
        if self.cap:
            self.cap.release()
        if self.sock:
            self.sock.close()
        logging.info("Resources released. Exiting.")

def main():
    parser = argparse.ArgumentParser(description='Holistic Tracker for AvatarStream')
    parser.add_argument('--camera', type=int, default=0, help='Camera index')
    parser.add_argument('--ip', type=str, default="127.0.0.1", help='UDP Target IP')
    parser.add_argument('--port', type=int, default=5005, help='UDP Target Port')
    parser.add_argument('--width', type=int, default=None, help='Camera capture width')
    parser.add_argument('--height', type=int, default=None, help='Camera capture height')
    parser.add_argument('--no-mirror', action='store_true', help='Disable camera mirroring')

    args = parser.parse_args()

    tracker = HolisticTracker(
        camera_idx=args.camera,
        udp_ip=args.ip,
        udp_port=args.port,
        width=args.width,
        height=args.height,
        no_mirror=args.no_mirror
    )
    tracker.run()

if __name__ == "__main__":
    main()
