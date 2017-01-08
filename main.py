import os

import sys
from gmusicapi import Mobileclient
import configparser
import requests
import vlc
from mainwindow import *

is_stream = True

class GMusicDownloader:
    api = None
    chunk_size = None
    file_type = None
    music_directory = None

    def __init__(self):
        config = configparser.ConfigParser()
        config.read("config.ini")
        account = config["Account"]
        self.load_settings(config["Settings"])
        if self.gui_enabled:
            self.gui()
        # self.api = Mobileclient()
        # print("GMusicDownloader initialised")
        # self.api.login(account["username"], account["password"], Mobileclient.FROM_MAC_ADDRESS)
        # print("logged in")
        # library = self.api.get_all_songs()
        # tracks = [track for track in library if track['artist'] == "Flume"]
        # for i in range(0,10):
        #     self.stream_download(tracks[i])
        # print("downloads complete")

    def get_directory_path(self, track):
        artist = track["artist"]
        album = track["album"]
        artist_path = os.path.join(self.music_directory, artist)
        album_path = os.path.join(artist_path, album)
        if not os.path.exists(artist_path):
            os.makedirs(artist_path)
        if not os.path.exists(album_path):
            os.makedirs(album_path)
        return album_path

    def stream_download(self, track):
        track_title = track["title"]

        directory_path = self.get_directory_path(track)
        file_path = os.path.join(directory_path, track_title + self.file_type)

        if not os.path.exists(file_path):
            dl = 0
            slowdown = 0
            print("downloading " + track_title, end="")
            track_url = self.api.get_stream_url(track['id'])
            response = requests.get(track_url, stream=True)
            total_length = int(response.headers.get('content-length'))
            with open(file_path, "wb") as songfile:
                for chunk in response.iter_content(chunk_size=self.chunk_size):
                    songfile.write(chunk)
                    dl += len(chunk)
                    slowdown += 1
                    if slowdown%20 == 0:
                        print(".", end="")
            print(" done.")
        else:
            print(track_title + " already exists, skipping")

    def load_settings(self, settingsDict):
        self.chunk_size = settingsDict.getint("chunk_size")
        self.file_type = "." + settingsDict["file_type"]
        self.music_directory = settingsDict["music_directory"]
        self.gui_enabled = settingsDict.getboolean("gui_enabled")

    def gui(self):
        import tkinter as tk

        root = tk.Tk()
        window = Mainwindow(root)
        window.run()






if __name__ == "__main__":
    GMusicDownloader()