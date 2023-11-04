import time
import socket
import sys
import pychromecast
from pychromecast.controllers.media import MediaStatusListener
from pychromecast.controllers.receiver import CastStatusListener


def send_udp_message(udp_message):
    print(udp_message)


class MyCastStatusListener(CastStatusListener):
    """Cast status listener"""

    def __init__(self, name, cast):
        self.name = name
        self.cast = cast

    def new_cast_status(self, status):
        print(f"[{time.ctime()} - {self.name}] status chromecast change: {status}")

        volume = int(round(status.volume_level * 100))
        app_name = status.display_name

        send_udp_message(f"{self.name}/volume/{volume}")

        if app_name:
            send_udp_message(f"{self.name}/app/{app_name}")


class MyMediaStatusListener(MediaStatusListener):
    """Status media listener"""

    def __init__(self, name, cast):
        self.name = name
        self.cast = cast

    def new_media_status(self, status):
        print(f"[{time.ctime()} - {self.name}] status media change: {status}")

        volume = int(round(status.volume_level * 100))
        artist = status.artist
        song = status.title
        album = status.album_name
        playback_status = status.player_state

        send_udp_message(f"{self.name}/volume/{volume}")

        if artist:
            send_udp_message(f"{self.name}/artist/{artist}")
        if song:
            send_udp_message(f"{self.name}/song/{song}")
        if album:
            send_udp_message(f"{self.name}/album/{album}")
        if playback_status:
            send_udp_message(f"{self.name}/status/{playback_status}")

    def load_media_failed(self, item, error_code):
        print(
            "[",
            time.ctime(),
            " - ",
            self.name,
            "] load media filed for item: ",
            item,
            " with code: ",
            error_code,
        )


# Function to handle incoming UDP commands
def handle_udp_commands(data):
    data = data.decode('utf-8')
    print(f"Request received: {data}")
    command = data.strip().split('/')

    if len(command) == 3:
        cast_name, cmd, value = command
        cast_name = cast_name.strip()
        cmd = cmd.strip()

        for chromecast in chromecasts:
            if chromecast.name == cast_name:
                if cmd == "play":
                    chromecast.media_controller.play()
                elif cmd == "pause":
                    chromecast.media_controller.pause()
                elif cmd == "stop":
                    chromecast.media_controller.stop()
                elif cmd == "next":
                    chromecast.media_controller.skip()
                elif cmd == "rewind":
                    chromecast.media_controller.rewind()
                elif cmd == "spotify":
                    chromecast.start_app("CC32E753")
                elif cmd == "incvol":
                    chromecast.volume_up()
                elif cmd == "decvol":
                    chromecast.volume_down()
                elif cmd == "setvol" and value.isdigit():
                    volume = int(value)
                    if 0 <= volume <= 100:
                        chromecast.set_volume(volume / 100)


chromecasts, browser = pychromecast.get_chromecasts()

if not chromecasts:
    print(f'No chromecasts discovered')
    sys.exit(1)

for chromecast in chromecasts:
    # Start socket client's worker thread and wait for initial status update
    chromecast.wait()

    listenerCast = MyCastStatusListener(chromecast.name, chromecast)
    chromecast.register_status_listener(listenerCast)

    listenerMedia = MyMediaStatusListener(chromecast.name, chromecast)
    chromecast.media_controller.register_status_listener(listenerMedia)

# Create a UDP socket
my_hostname = socket.gethostname()
my_ip_address = socket.gethostbyname(my_hostname)
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.bind((my_ip_address, 4444))

try:
    while True:
        print("####### Server is listening #######")
        data, address = s.recvfrom(4096)
        handle_udp_commands(data)
except KeyboardInterrupt:
    # Shut down discovery
    browser.stop_discovery()
