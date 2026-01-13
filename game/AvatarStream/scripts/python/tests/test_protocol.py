import unittest
import socket
import struct
import threading
import time
import os
import numpy as np

# Mock implementation of the binary protocol
class TestBinaryProtocol(unittest.TestCase):
    def test_pose_data_parsing(self):
        """
        Verify that we can pack pose data in Python and it matches the expected structure.
        We can't easily test Godot parsing here without running Godot, but we can verify
        the Python side packing logic.
        """
        landmarks = []
        for i in range(33):
            landmarks.append({'x': 0.1, 'y': 0.2, 'z': 0.3, 'visibility': 0.9})

        flattened = []
        for lm in landmarks:
            flattened.extend([lm['x'], lm['y'], lm['z'], lm['visibility']])

        message = struct.pack(f'{len(flattened)}f', *flattened)

        # Check size: 33 landmarks * 4 floats * 4 bytes = 528 bytes
        self.assertEqual(len(message), 528)

        # Verify unpacking
        unpacked = struct.unpack(f'{len(flattened)}f', message)
        self.assertEqual(len(unpacked), 132)
        self.assertAlmostEqual(unpacked[0], 0.1, places=5)

    def test_video_frame_protocol(self):
        """
        Test the image receiving logic used in holistic_tracker.py
        Simulate a server and a client.
        """

        # We need to simulate the "Server" (holistic_tracker.py) receiving data from Godot.
        # But holistic_tracker.py actually acts as a Server.
        # Wait, holistic_tracker.py: server_sock.listen(1). It waits for Godot (client) to connect.
        # So we act as the Client (Godot) here.

        server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_sock.bind(("127.0.0.1", 0)) # Random port
        server_sock.listen(1)
        port = server_sock.getsockname()[1]

        def server_thread_func():
            conn, addr = server_sock.accept()
            with conn:
                # Read width and height
                header_data = b''
                while len(header_data) < 8:
                    packet = conn.recv(8 - len(header_data))
                    if not packet: break
                    header_data += packet

                width = int.from_bytes(header_data[0:4], byteorder='little')
                height = int.from_bytes(header_data[4:8], byteorder='little')

                size = width * height * 3

                # Read data
                data = b''
                while len(data) < size:
                    packet = conn.recv(size - len(data))
                    if not packet: break
                    data += packet

                # Verify data
                expected_size = 640 * 360 * 3
                if size == expected_size and width == 640 and height == 360:
                     frame = np.frombuffer(data, dtype=np.uint8)
                     if len(frame) == expected_size:
                         return True
                return False

        t = threading.Thread(target=server_thread_func)
        t.start()

        # Client (Godot simulation)
        time.sleep(0.1)
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(("127.0.0.1", port))

        # Send raw RGB frame (640x360)
        w, h = 640, 360
        frame_data = bytearray(os.urandom(w * h * 3))

        # Protocol: Width (4), Height (4), Data
        client.sendall(struct.pack('<II', w, h))
        client.sendall(frame_data)

        client.close()
        t.join()
        server_sock.close()

if __name__ == '__main__':
    import os
    unittest.main()
