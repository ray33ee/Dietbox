from textual.app import App, ComposeResult
from textual.containers import HorizontalGroup, VerticalScroll
from textual.widgets import Footer, Header, Button, Label, RadioButton, RadioSet
import subprocess
import os

download_directory = '/mnt/dietpi_userdata/downloads/'

items = []

transmission_username = "root"
transmission_password = "dietpi"

list_torrent_result = subprocess.run(['transmission-remote', '-n' + transmission_username + ":" + transmission_password, '-l'], capture_output=True, text=True)

if list_torrent_result.returncode != 0:
    if list_torrent_result.returncode == 1:
        print("Bad transmission username or password")
        exit(1)

raw_torrent_list = list_torrent_result.stdout

lines = raw_torrent_list.split('\n')

# Because of the way the table is formated, the index of 'Name' will be the start index of the name of every torrent in every subsequent line
name_position = lines[0].index('Name')

for i, line in enumerate(lines[1:-2]):
    torrent_title = line[name_position:]
    full_path = os.path.join(download_directory, torrent_title)
    # If the torrent is in the downloads folder then add it to the list
    if os.path.exists(full_path):
        items.append({"name": torrent_title, "choice": "leave", "id": i+1})

class ItemSelectorWidget(HorizontalGroup):

    def compose(self):
        yield Button("<", id="previous")
        yield Label("", id="total")
        yield Button(">", id="next")


class TorrentMoverApp(App):

    BINDINGS = [("d", "toggle_dark", "Toggle dark mode")]

    def __init__(self, iterable):
        self.l = list(iterable)
        self.index = 0
        super().__init__()

    def on_button_pressed(self, event):
        button_id = event.button.id
        if button_id == "next":
            if self.index != len(items)-1:
                self.index += 1
                self.display_torrent()
        elif button_id == "previous":
            if self.index != 0:
                self.index -= 1
                self.display_torrent()
        elif button_id == "final":
            self.exit()
            for item in items:
                if (item["choice"] != "leave"):
                    r = subprocess.run(['transmission-remote', '-n' + transmission_username + ":" + transmission_password, '-t', str(item['id']), "--move", "/mnt/dietpi_userdata/" +  item["choice"]], capture_output=True, text=True)
                    if (r.returncode != 0):
                        print("Bad --move subprocess return code")
                        app.exit()
                    self.notify("Torrent '" + item["name"] + "' (" + str(item["id"]) + ") - " + item["choice"])
            # Then at the end ask the user if they want to rescan their plex library
            subprocess.run(['/usr/lib/plexmediaserver/Plex Media Scanner', '-a'])

    def format_label(self):
        return str(self.index+1) + "/" + str(len(self.l))

    def display_torrent(self):
        self.query_one('#total').update(self.format_label())
        self.query_one('#torrent_name').update(items[self.index]['name'])
        self.query_one('#' + items[self.index]["choice"]).value = True

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        yield Footer()
        yield ItemSelectorWidget()
        yield Label("", id="torrent_name")
        with RadioSet():
           yield RadioButton("Movies", id='Movies')
           yield RadioButton("TV", id='Shows')
           yield RadioButton("Audiobooks", id='Audiobooks')
           yield RadioButton("Radios", id='radios')
           yield RadioButton("Misc", id='misc')
           yield RadioButton("Software", id='Software')
           yield RadioButton("Books", id='Books')
           yield RadioButton("Music", id='Music')
           yield RadioButton("Do not move", id="leave")
        yield Button("Finalise", id="final")

    def on_mount(self):
        self.display_torrent()

    def on_radio_set_changed(self, event):
        items[self.index]["choice"] = event.pressed.id

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.theme = (
            "textual-dark" if self.theme == "textual-light" else "textual-light"
        )


if __name__ == "__main__":
    app = TorrentMoverApp(items)
    app.run()
