import configparser
import os
import threading
import requests
from queue import Queue

from gmusicapi import Mobileclient


class GMusicDownloader(threading.Thread):
    api = None
    library = list()
    filtered_library = list()
    max_threads = None

    def __init__(self, queue: Queue):
        super().__init__()
        self.communicationqueue = queue
        self.api = Mobileclient()
        config = configparser.ConfigParser()
        config.read("config.ini")
        self.load_settings(config)
        threading.Thread(target=self.login).start()

    def login(self):
        self.api.login(self.username, self.password, Mobileclient.FROM_MAC_ADDRESS)
        print("logged in")
        self.library = self.api.get_all_songs()
        print("songs fetched")
        self.communicationqueue.put({"login": self.username,
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

    def threaded_stream_downloads(self, tracklist: list):
        self.trackqueue = Queue()
        for i in range(self.max_threads):
            threading.Thread(target=self.__downloadworker).start()
        for track in tracklist:
            self.trackqueue.put(track)
        #stop threads when they're done
        for i in range(self.max_threads):
            self.trackqueue.put(None)

    def __downloadworker(self):
        while True:
            track = self.trackqueue.get()
            if track is None:
                break
            self.communicationqueue.put({"downloading": track})
            self.stream_download(track)
            self.trackqueue.task_done()


    def stream_download(self, track: dict):
        track_title = track["title"]

        directory_path = self.get_directory_path(self.music_directory, track)
        file_path = os.path.join(directory_path, track_title + self.file_type)

        if not os.path.exists(file_path):
            dl = 0
            track_url = self.api.get_stream_url(track['id'])
            response = requests.get(track_url, stream=True)
            total_length = int(response.headers.get('content-length'))
            with open(file_path, "wb") as songfile:
                for chunk in response.iter_content(chunk_size=self.chunk_size):
                    songfile.write(chunk)
                    dl += len(chunk)
            print(track_title, " done.")
            # next(filter(lambda t: t == track, self.filtered_library))
            self.communicationqueue.put({"download complete": track})
        else:
            print(track_title + " already exists, skipping")

    def search_library(self, searchterm: str):
        if searchterm == "*":
            self.filtered_library = self.library
        else:
            self.filtered_library = list(filter(lambda t: searchterm in t["artist"], self.library))

    def track_already_downloaded(self, track: dict):
        return os.path.exists(
            os.path.join(self.music_directory, track["artist"], track["album"], track["title"] + self.file_type))

    def check_filtered_tracks_for_download(self):
        for track in self.filtered_library:
            if "saved" not in track:
                if self.track_already_downloaded(track):
                    track["saved"] = "√"
                else:
                    track["saved"] = ""

    def sort_filtered_library(self, sort: str, reversed: bool):
        self.filtered_library = sorted(self.filtered_library, key= lambda k: k[sort], reverse=reversed)

    def load_settings(self, config: configparser.ConfigParser):
        account = config["Account"]
        self.username = account["username"]
        self.password = account["password"]
        settings = config["Settings"]
        self.music_directory = settings["music_directory"]
        self.file_type = "." + settings["file_type"]
        self.chunk_size = settings.getint("chunk_size")
        self.max_threads = settings.getint("download_threads", 5)
