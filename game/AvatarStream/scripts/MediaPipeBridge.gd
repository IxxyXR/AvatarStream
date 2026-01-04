extends Node

var udp = PacketPeerUDP.new()
var pose_landmarks = []
var python_pid = -1
var config = ConfigFile.new()
var settings_path = "user://settings.cfg"

func _ready():
	# Load settings
	var err = config.load(settings_path)
	if err != OK:
		# If file doesn't exist or is corrupt, create defaults
		config.set_value("camera", "index", 0)
		config.set_value("camera", "width", 1280)
		config.set_value("camera", "height", 720)
		config.set_value("camera", "mirror", true)
		config.set_value("network", "ip", "127.0.0.1")
		config.set_value("network", "port", 5005)
		config.save(settings_path)
		print("Created new settings file at: ", ProjectSettings.globalize_path(settings_path))

	var camera_index = config.get_value("camera", "index", 0)
	var camera_width = config.get_value("camera", "width", 1280)
	var camera_height = config.get_value("camera", "height", 720)
	var camera_mirror = config.get_value("camera", "mirror", true)
	var udp_ip = config.get_value("network", "ip", "127.0.0.1")
	var udp_port = config.get_value("network", "port", 5005)

	if udp.listen(udp_port) != OK:
		print("Error listening on port: ", udp_port)
		return

	print("Listening on port: ", udp_port)

	var python_script_path = ProjectSettings.globalize_path("res://scripts/python/holistic_tracker.py")

	# Construct arguments
	var args = ["-u", python_script_path]
	args.append("--camera")
	args.append(str(camera_index))
	args.append("--ip")
	args.append(udp_ip)
	args.append("--port")
	args.append(str(udp_port))

	if camera_width > 0:
		args.append("--width")
		args.append(str(camera_width))
	if camera_height > 0:
		args.append("--height")
		args.append(str(camera_height))

	if not camera_mirror:
		args.append("--no-mirror")

	# For Windows, it's often 'python.exe', but 'python' should work if it's in PATH.
	# For macOS and Linux, it could be 'python' or 'python3'.
	var python_executable = "python"

	# Try python first
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
	if udp.get_available_packet_count() > 0:
		var packet = udp.get_packet()
		var data_string = packet.get_string_from_utf8()

		var json = JSON.new()
		var error = json.parse(data_string)
		if error == OK:
			var data = json.get_data()
			if data.has("pose_landmarks"):
				pose_landmarks = data["pose_landmarks"]
		else:
			print("JSON Parse Error: ", json.get_error_message(), " in ", data_string)

func get_pose_landmarks():
	return pose_landmarks

func _notification(what):
	if what == MainLoop.NOTIFICATION_WM_CLOSE_REQUEST:
		if python_pid > 0 and OS.is_process_running(python_pid):
			OS.kill(python_pid)
			print("Killed python process with PID: ", python_pid)
		udp.close()
