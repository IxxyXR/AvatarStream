extends Node

# Use TCP for reliable stream (better for larger frames than UDP)
var tcp_client := StreamPeerTCP.new()
var dest_ip := "127.0.0.1"
var dest_port := 5006
var frame_rate := 30.0
var time_since_last_frame := 0.0
var connected := false

var target_width := 640
var target_height := 360

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

func set_resolution(width: int, height: int):
    target_width = width
    target_height = height
    print("Virtual Camera resolution set to: " + str(width) + "x" + str(height))

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
    image.resize(target_width, target_height)

    # Convert to RGB8 if needed (pyvirtualcam expects RGB)
    if image.get_format() != Image.FORMAT_RGB8:
        image.convert(Image.FORMAT_RGB8)

    # Get raw data (much faster than JPG encoding)
    var buffer = image.get_data()

    if buffer.size() > 0:
        # Send width (4 bytes), height (4 bytes), then data
        tcp_client.put_32(target_width)
        tcp_client.put_32(target_height)
        tcp_client.put_data(buffer)
