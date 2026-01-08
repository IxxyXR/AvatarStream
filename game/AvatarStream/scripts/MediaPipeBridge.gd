extends Node

var udp = PacketPeerUDP.new()
var pose_landmarks = []
var python_pid = -1

func _ready():
	# The port should match the one in the Python script
	var port = 5005
	if udp.listen(port) != OK:
		print("Error listening on port: ", port)
		return

	print("Listening on port: ", port)

	var python_script_path = ProjectSettings.globalize_path("res://scripts/python/holistic_tracker.py")
	var args = ["-u", python_script_path]

	# For Windows, it's often 'python.exe', but 'python' should work if it's in PATH.
	# For macOS and Linux, it could be 'python' or 'python3'.
	var python_executable = "python"

	if OS.get_environment("AVATARSTREAM_LAUNCHED_BY_RUNNER") == "1":
		print("Launched by run.py, skipping Python tracker auto-start.")
	else:
		python_pid = OS.execute(python_executable, args, false) # non-blocking

		if python_pid == 0 or python_pid == -1: # 0 or -1 indicates failure
			print("Error starting python script with 'python'. Trying 'python3'.")
			python_executable = "python3"
			python_pid = OS.execute(python_executable, args, false) # non-blocking
			if python_pid == 0 or python_pid == -1:
				 print("Error starting python script with 'python3' as well. Please check your python installation and PATH.")
			else:
				print("Python script started with PID: ", python_pid)
		else:
			print("Python script started with PID: ", python_pid)


func _process(_delta):
	while udp.get_available_packet_count() > 0:
		var packet = udp.get_packet()
		# Expecting binary data: 33 landmarks * 4 floats * 4 bytes/float = 528 bytes
		# Format: x, y, z, visibility (all float32)
		if packet.size() % 16 == 0:
			var count = packet.size() / 16
			pose_landmarks = []
			var spb = StreamPeerBuffer.new()
			spb.data_array = packet

			for i in range(count):
				var lm = {}
				lm['x'] = spb.get_float()
				lm['y'] = spb.get_float()
				lm['z'] = spb.get_float()
				lm['visibility'] = spb.get_float()
				pose_landmarks.append(lm)
		else:
			# Fallback to JSON for compatibility or logging
			var data_string = packet.get_string_from_utf8()
			var json = JSON.new()
			var error = json.parse(data_string)
			if error == OK:
				var data = json.get_data()
				if data.has("pose_landmarks"):
					pose_landmarks = data["pose_landmarks"]
			else:
				print("Packet Error: Invalid binary size and JSON parse failed.")

func get_pose_landmarks():
	return pose_landmarks

func _notification(what):
	if what == MainLoop.NOTIFICATION_WM_CLOSE_REQUEST:
		if python_pid > 0 and OS.is_process_running(python_pid):
			OS.kill(python_pid)
			print("Killed python process with PID: ", python_pid)
		udp.close()
