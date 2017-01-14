import configparser
import os
import re
import threading
import requests
from queue import Queue
import unicodedata
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3NoHeaderError
from mutagen.mp3 import MP3
import mutagen

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

    def get_directory_path(self, track: dict, and_create = False):
        artist = self.slugify(track["artist"])
        album = self.slugify(track["album"])
        artist_path = os.path.join(self.music_directory, artist)
        album_path = os.path.join(artist_path, album)
        if and_create:
            if not os.path.exists(artist_path):
                os.makedirs(artist_path)
            if not os.path.exists(album_path):
                os.makedirs(album_path)
        return album_path

    def get_file_path(self, track: dict, directory_path: str = None):
        if directory_path is not None:
            return os.path.join(directory_path, self.slugify(track["title"]) + self.file_type)
        else:
            return os.path.join(self.get_directory_path(track), self.slugify(track["title"]) + self.file_type)

    def threaded_stream_downloads(self, tracklist: list):
        self.trackqueue = Queue()
        self.filecreationlock = threading.Lock()
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

        self.filecreationlock.acquire()
        directory_path = self.get_directory_path(track, and_create=True)
        self.filecreationlock.release()

        file_path = self.get_file_path(track, directory_path)

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
        else:
            print(track_title + " already exists, skipping")
        self.add_tags(file_path, track)
        self.communicationqueue.put({"download complete": track})

    def search_library(self, searchterm: str):
        if searchterm == "*":
            self.filtered_library = self.library
        else:
            self.filtered_library = list(filter(lambda t: searchterm in t["artist"], self.library))

    def search_gmusic(self, searchstring: str):
        threading.Thread(target=self.__search_worker_thread, args= (searchstring,)).start()

    def __search_worker_thread(self, searchstring: str):
        searchresults = self.api.search(searchstring.encode("utf-8").decode("utf-8"))
        self.filtered_library = list(map(self.parse_song_hit, searchresults["song_hits"]))
        self.communicationqueue.put({"search results": True})

    @staticmethod
    def parse_song_hit(song_hit):
        """
        couldn't fit it into a lambda :'(
        """
        track = song_hit["track"]
        track["id"] = track["storeId"]
        return track

    @staticmethod
    def slugify(value):
        """
        Normalizes string, removes non-alpha characters
        """
        value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('utf-8')
        value = re.sub('[^\w\s-]', '', value).strip()
        return value

    def check_filtered_tracks_for_download(self):
        for track in self.filtered_library:
            if "saved" not in track:
                if os.path.exists(self.get_file_path(track)):
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

    def add_tags(self, filepath: str, track: dict):
        try:
            tags = EasyID3(filepath)
        except ID3NoHeaderError:
            tags = mutagen.File(filepath, easy=True)
            tags.add_tags()

        tags["tracknumber"] = str(track["trackNumber"]).encode("utf-8").decode("utf-8")
        tags["title"] = track["title"]
        tags["artist"] = track["artist"]
        tags["album"] = track["album"]
        tags["discnumber"] = str(track["discNumber"]).encode("utf-8").decode("utf-8")
        tags["genre"] = track["genre"]
        tags["composer"] = track["composer"]
        tags["albumartist"] = track["albumArtist"]
        if "beatsPerMinute" in track:
            tags["bpm"] = track["beatsPerMinute"]
        tags.save(v2_version=3)



