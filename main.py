import os
import configparser
import threading
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

    def __init__(self):
        config = configparser.ConfigParser()
        config.read("config.ini")
        self.load_settings(config["Settings"])

        self.queue = queue = Queue()
        self.downloader = GMusicDownloader(queue)


        if self.gui_enabled:
            self.guiroot = guiroot = tk.Tk()
            self.poll_downloader()
            self.mainwindow = window = Mainwindow(self, guiroot)
            window.run()

                # for i in range(0,10):
                #     self.stream_download(tracks[i])
                # print("downloads complete")

    def poll_downloader(self):
        while self.queue.qsize():
            try:
                msg = self.queue.get(0) #type: dict
                if "login" in msg:
                    self.login_complete(msg["login"])
                if "download complete" in msg:
                    self.download_complete(msg["download complete"])
            except Empty:
                pass
        self.guiroot.after(100, self.poll_downloader)

    def got_search_query(self, query):
        print("application queried", query)

        if self.gui_enabled:
            self.mainwindow.treeview.delete(*self.mainwindow.treeview.get_children())

        if query == "*":
            self.tracks = self.downloader.library
        else:
            self.tracks = self.downloader.search_library(query)

        if self.gui_enabled:
            for track in self.tracks:
                if self.downloader.track_already_downloaded(track):
                   track["saved"] = "√"
                else:
                    track["saved"] = ""
                self.mainwindow.insert_track(track)

        else:
            print([track["title"] for track in self.library if track['artist'] in query])

    def download_selection(self, selecteditems: tuple):
        for trackid in selecteditems:
            track = [track for track in self.tracks if track["id"] == trackid][0]
            self.downloader.stream_download(track)

    def download_complete(self, track: dict):
        if self.gui_enabled:
            self.mainwindow.track_download_complete(track)

    def login_complete(self, username: str):
        self.mainwindow.loggedinlabel.set("Logged in as " + username)
        self.got_search_query("*")


    def load_settings(self, configsettings):
        self.gui_enabled = configsettings.getboolean("gui_enabled")


if __name__ == "__main__":
    Application()