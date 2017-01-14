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


    def __init__(self):
        config = configparser.ConfigParser()
        config.read("config.ini")
        self.load_settings(config)

        self.communicationqueue = Queue()
        self.downloader = GMusicDownloader(self.communicationqueue)

        if self.gui_enabled:
            self.guiroot = guiroot = tk.Tk()
            self.poll_downloader()
            self.mainwindow = window = Mainwindow(self, guiroot)
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

            except Empty:
                pass
        if self.gui_enabled:
            self.guiroot.after(100, self.poll_downloader)
        else:
            pass
            #TODO make this work with a different main loop

    def got_search_query(self, query: str):

        self.downloader.search_library(query)
        self.update_user_with_filtered_tracks()


    def download_selection(self, selecteditems: tuple):
        self.requested_downloads = len(selecteditems)
        self.complete_and_in_progress_downloads = 0
        self.mainwindow.update_download_count(self.complete_and_in_progress_downloads, self.requested_downloads)
        downloadtracks = list()
        for trackid in selecteditems:
            #will get the full track object that matches the track id
            track = next(filter(lambda t: t["id"] == trackid, self.downloader.filtered_library))
            downloadtracks.append(track)
        self.downloader.threaded_stream_downloads(downloadtracks)

    def download_complete(self, track: dict):
        if self.gui_enabled:
            self.mainwindow.track_download_complete(track)
            if self.complete_and_in_progress_downloads == self.requested_downloads:
                self.mainwindow.update_download_count(complete=True)

    def login_complete(self, username: str):
        self.mainwindow.display_loggedin_user(username)
        self.got_search_query("*")

    def load_settings(self, configsettings):
        settings = configsettings["Settings"]
        self.gui_enabled = settings.getboolean("gui_enabled")

    def sort(self, column: str):
        #so that you can click on the column and have it reverse on the second click
        if column in self.lastsort:
            self.lastsort = {column: not self.lastsort[column]}
        else:
            self.lastsort = {column: False}
        self.downloader.sort_filtered_library(column, self.lastsort[column])
        self.update_user_with_filtered_tracks()

    def update_user_with_filtered_tracks(self):
        if self.gui_enabled:
            self.downloader.check_filtered_tracks_for_download()
            self.mainwindow.clear_tracks()
            self.mainwindow.insert_tracks(self.downloader.filtered_library)
        else:
            print([track["title"] for track in self.downloader.filtered_library])

    def update_user_with_downloading(self, track):
        self.mainwindow.update_current_downloads(track["title"])
        self.complete_and_in_progress_downloads += 1
        self.mainwindow.update_download_count(self.complete_and_in_progress_downloads, self.requested_downloads)

    def search_gmusic(self, searchstring: str):
        self.downloader.search_gmusic(searchstring)


if __name__ == "__main__":
    Application()
