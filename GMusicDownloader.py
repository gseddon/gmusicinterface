import configparser
import os
import threading
from time import sleep

import requests
from queue import Queue
from queue import Empty

from gmusicapi import Mobileclient


class GMusicDownloader(threading.Thread):
    api = None
    library = list()

    def __init__(self, queue: Queue):
        super().__init__()
        self.queue = queue
        self.api = Mobileclient()
        config = configparser.ConfigParser()
        config.read("config.ini")
        self.load_settings(config)
        self.thread = threading.Thread(target=self.login)
        self.thread.start()

    def login(self):
        self.api.login(self.username, self.password, Mobileclient.FROM_MAC_ADDRESS)
        print("logged in")
        self.library = self.api.get_all_songs()
        print("songs fetched")
        self.queue.put({"login": self.username,
                        "library": self.library})

    @staticmethod
    def get_directory_path(music_directory: str, track: dict):
        artist = track["artist"]
        album = track["album"]
        artist_path = os.path.join(music_directory, artist)
        album_path = os.path.join(artist_path, album)
        if not os.path.exists(artist_path):
            os.makedirs(artist_path)
        if not os.path.exists(album_path):
            os.makedirs(album_path)
        return album_path

    def poll_queue(self):
        while self.queue.qsize():
            try:
                msg = self.queue.get(0) #type: dict
                print(msg)
            except Empty:
                pass

    def threaded_stream_download(self, track):
        threading.Thread(target=self.stream_download, args=(track,)).start()

    def stream_download(self, track):
        track_title = track["title"]

        directory_path = self.get_directory_path(self.music_directory, track)
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
            self.queue.put({"download complete": track})
        else:
            print(track_title + " already exists, skipping")

    def search_library(self, searchterm: str):
        return [track for track in self.library if searchterm in track['artist']]


    def track_already_downloaded(self, track: dict):
        return os.path.exists(
            os.path.join(self.music_directory, track["artist"], track["album"], track["title"] + self.file_type))

    def load_settings(self, config: configparser.ConfigParser):
        account = config["Account"]
        self.username = account["username"]
        self.password = account["password"]
        settings = config["Settings"]
        self.music_directory = settings["music_directory"]
        self.file_type = "." + settings["file_type"]
        self.chunk_size = settings.getint("chunk_size")
