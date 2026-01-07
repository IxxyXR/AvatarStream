extends Node

# Use TCP for reliable stream (better for larger frames than UDP)
var tcp_client := StreamPeerTCP.new()
var dest_ip := "127.0.0.1"
var dest_port := 5006
var frame_rate := 30.0
var time_since_last_frame := 0.0
var connected := false

func _ready():
    # Only enable on desktop platforms
    if not (OS.get_name() in ["Windows", "macOS", "Linux", "FreeBSD", "NetBSD", "OpenBSD", "BSD"]):
        set_process(false)
        print("Virtual Camera Sender disabled on non-desktop platform: " + OS.get_name())
        return

    connect_to_server()

func connect_to_server():
    var err = tcp_client.connect_to_host(dest_ip, dest_port)
    if err == OK:
        print("Connecting to Virtual Camera Server at " + dest_ip + ":" + str(dest_port))
        connected = true
    else:
        print("Failed to connect to Virtual Camera Server.")
        connected = false

func _process(delta):
    # Check connection status
    tcp_client.poll()
    var status = tcp_client.get_status()
    if status == StreamPeerTCP.STATUS_CONNECTED:
        connected = true
    elif status == StreamPeerTCP.STATUS_NONE or status == StreamPeerTCP.STATUS_ERROR:
        connected = false
        # Reconnect logic could go here, but keep simple for now
        # connect_to_server()

    time_since_last_frame += delta
    if time_since_last_frame < 1.0 / frame_rate:
        return

    time_since_last_frame = 0.0
    if connected:
        send_frame()

func send_frame():
    var viewport = get_viewport()
    if not viewport:
        return

    var image = viewport.get_texture().get_image()
    # Resize to something reasonable for streaming
    image.resize(640, 360)

    # Convert to JPG
    var buffer = image.save_jpg_to_buffer(0.75)

    if buffer.size() > 0:
        # Send size first (4 bytes), then data
        tcp_client.put_32(buffer.size())
        tcp_client.put_data(buffer)
