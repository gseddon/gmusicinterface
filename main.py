import configparser
from queue import Queue
from queue import Empty
import tkinter as tk
from GMusicDownloader import GMusicDownloader
from mainwindow import *


class Application:
    chunk_size = None
    file_type = None
    music_directory = None
    library = None
    tracks = set()
    executor = None
    guiroot = None
    lastsort = {}
    requested_downloads = None
    complete_and_in_progress_downloads = None
    gui_enabled = True

    def __init__(self):
        config = configparser.ConfigParser()
        config.read("config.ini")
        self.load_settings(config)

        self.communicationqueue = Queue()
        self.downloader = GMusicDownloader(self.communicationqueue)

        if self.gui_enabled:
            self.guiroot = guiroot = tk.Tk()
            self.mainwindow = window = Mainwindow(self, guiroot)
            self.poll_downloader()
            window.run()

    def poll_downloader(self):
        while self.communicationqueue.qsize():
            try:
                msg = self.communicationqueue.get(0)  # type: dict
                if "login" in msg:
                    self.login_complete(msg["login"])
                if "download complete" in msg:
                    self.download_complete(msg["download complete"])
                if "downloading" in msg:
                    self.update_user_with_downloading(msg["downloading"])
                if "search results" in msg:
                    self.update_user_with_filtered_tracks()
                if "ConfigError" in msg:
                    self.update_user_with_error(msg["ConfigError"])
                if "playlists loaded" in msg:
                    self.display_playlists()
            except Empty:
                pass
        if self.gui_enabled:
            self.guiroot.after(100, self.poll_downloader)
        else:
            pass
            # TODO make this work with a different main loop

    def got_search_query(self, query: str):

        self.downloader.search_library(query)
        self.update_user_with_filtered_tracks()

    def download_selection(self, selected_items: tuple):
        self.requested_downloads = len(selected_items)
        self.complete_and_in_progress_downloads = 0
        if self.gui_enabled:
            self.mainwindow.update_download_count(self.complete_and_in_progress_downloads, self.requested_downloads)
        download_tracks = list()
        for track_id in selected_items:
            # will get the full track object that matches the track id
            track = next(filter(lambda t: t["id"] == track_id, self.downloader.filtered_library))
            download_tracks.append(track)
        self.downloader.threaded_stream_downloads(download_tracks)

    def download_complete(self, track: dict):
        if self.gui_enabled:
            self.mainwindow.track_download_complete(track)
            if self.complete_and_in_progress_downloads == self.requested_downloads:
                self.mainwindow.update_download_count(complete=True)

    def login_complete(self, username: str):
        self.mainwindow.display_loggedin_user(username)
        self.got_search_query("*")

    def load_settings(self, configsettings):
        try:
            settings = configsettings["Settings"]
            self.gui_enabled = settings.getboolean("gui_enabled")
        except KeyError as e:
            self.update_user_with_error({"title": "Configuration Error",
                                         "body": "Could not find " + e.args[
                                             0] + " in preferences, please update prefs and try again"})

    def reload_settings(self, configsettings):
        self.load_settings(configsettings)
        if self.gui_enabled:
            self.downloader.load_settings(configsettings)
            self.downloader.threaded_api_query(self.downloader.login)

    def sort(self, column: str, contenttype: str):
        # so that you can click on the column and have it reverse on the second click
        if column in self.lastsort:
            self.lastsort = {column: not self.lastsort[column]}
        else:
            self.lastsort = {column: False}
        self.downloader.sort(column, self.lastsort[column], contenttype)
        if contenttype == "Track":
            self.update_user_with_filtered_tracks()
        elif contenttype == "Playlist":
            self.display_playlists()

    def update_user_with_filtered_tracks(self):
        if self.gui_enabled:
            self.downloader.check_filtered_tracks_for_download()
            self.mainwindow.empty_treeview()
            self.mainwindow.insert_tracks(self.downloader.filtered_library)
        else:
            print([track["title"] for track in self.downloader.filtered_library])

    def update_user_with_downloading(self, track):
        self.mainwindow.update_current_downloads(track["title"])
        self.complete_and_in_progress_downloads += 1
        self.mainwindow.update_download_count(self.complete_and_in_progress_downloads, self.requested_downloads)

    def search_gmusic(self, search_string: str):
        self.downloader.threaded_api_query(self.downloader.search_worker_thread, search_string)

    def update_user_with_error(self, error: dict):
        if self.gui_enabled:
            self.mainwindow.update_user_with_error(error)

    def open_playlists(self):
        self.downloader.threaded_api_query(self.downloader.open_playlists)

    def display_playlists(self):
        if self.gui_enabled:
            self.mainwindow.display_playlists(self.downloader.playlists)

    def display_playlist(self, iid: str):
        self.downloader.threaded_api_query(self.downloader.all_playlists, iid)


if __name__ == "__main__":
    Application()
