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
import types

from gmusicapi import Mobileclient
from vlc import callbackmethod


class GMusicDownloader(threading.Thread):
    api = None
    library = list()
    filtered_library = list()
    max_threads = None
    config_error = False
    loggedin = False
    playlists = None
    fetchedlists = None  # type: list
    filecreationlock = None
    trackqueue = None
    player = None
    current_displayed_content_type = "Track"

    def __init__(self, queue: Queue):
        super().__init__()
        self.communicationqueue = queue
        self.api = Mobileclient()
        config = configparser.ConfigParser()
        config.read("config.ini")
        self.load_settings(config)
        if not self.config_error:
            self.threaded_api_query(self.login)

    def login(self):
        if not self.loggedin:
            self.api.login(self.username, self.password, Mobileclient.FROM_MAC_ADDRESS)
            print("logged in")
            self.library = self.api.get_all_songs()
            print("songs fetched")
            self.communicationqueue.put({"login": self.username,
                                         "library": self.library})
            self.loggedin = True

    def get_directory_path(self, track: dict, and_create=False):
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
        # stop threads when they're done
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
            # total_length = int(response.headers.get('content-length'))
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

    def search_library(self, search_term: str):
        if search_term == "*":
            self.filtered_library = self.library
        else:
            self.filtered_library = list(filter(lambda t: search_term in t["artist"], self.library))

    @staticmethod
    def threaded_api_query(worker: types.FunctionType, *args):
        threading.Thread(target=worker, args=(*args,)).start()

    def search_worker_thread(self, searchstring: str):
        search_results = self.api.search(self.slugify(searchstring))

        def parse_song_hit(song_hit):
            # couldn't fit it into a lambda :'(
            track = song_hit["track"]
            track["id"] = track["storeId"]
            return track

        self.filtered_library = list(map(parse_song_hit, search_results["song_hits"]))
        self.communicationqueue.put({"search results": True})

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

    def sort(self, sort: str, is_reversed: bool, content_type: str):
        if content_type == "Track":
            self.filtered_library = sorted(self.filtered_library, key=lambda k: k[sort], reverse=is_reversed)
        elif content_type == "Playlist":
            def lazy_hack_for_playlist_sort(playlist: dict):
                if sort == "title":
                    return playlist["name"]
                if sort == "artist":
                    return playlist["ownerName"]
                if sort == "album":
                    return playlist['type']

            self.playlists = sorted(self.playlists, key=lazy_hack_for_playlist_sort, reverse=is_reversed)

    def load_settings(self, config: configparser.ConfigParser):
        try:
            account = config["Account"]
            self.username = account["username"]
            self.password = account["password"]
            settings = config["Settings"]
            self.music_directory = settings["music_directory"]
            self.file_type = "." + settings["file_type"]
            self.chunk_size = settings.getint("chunk_size")
            self.max_threads = settings.getint("download_threads", 5)
            self.config_error = False
        except KeyError as e:
            self.communicationqueue.put({"error":
                                             {"title": "Configuration Error GMusicDownloader",
                                              "body": "Could not find " + e.args[0]
                                                      + " in preferences, please update prefs and try again"}})
            self.config_error = True

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
        if "beatsPerMinute" in track and not track["beatsPerMinute"] == 0:
            tags["bpm"] = str(track["beatsPerMinute"]).encode("utf-8").decode("utf-8")
        # TODO store Year. will have to use standard ID3 instead of easy
        tags.save(v2_version=3)

    def open_playlists(self):
        if self.playlists is None:
            self.playlists = self.api.get_all_playlists()
        if not "lastAdded" in map(lambda p: p["id"], self.playlists):
            self.add_automatic_playlists()
        self.communicationqueue.put({"playlists loaded": self.playlists})

    def add_automatic_playlists(self):
        last_added = {"id": 'lastAdded',
                     "tracks": sorted(self.library, key=lambda t: t['creationTimestamp'], reverse=True),
                     "name": "Last Added",
                     "ownerName": "System",
                     "type": "Automatic"}
        self.playlists.append(last_added)

        thumbs_up = {"id": 'thumbsup',
                     "tracks": filter(lambda t: t['rating'] > 3, self.library),
                     "name": "Thumbs Up",
                     "ownerName": "System",
                     "type": "Automatic"}
        self.playlists.append(thumbs_up)


    def fetch_all_playlists_and_return_one_with_iid(self, iid: str):
        # TODO make this work for non user owned playlists. should use get_shared_playlist_contents for those.
        if self.fetchedlists is None:
            self.fetchedlists = self.api.get_all_user_playlist_contents()  # type: list
            # noinspection PyTypeChecker
            for playlist in self.fetchedlists:
                existing_playlist = next(filter(lambda p: p["id"] == playlist["id"], self.playlists))
                existing_playlist["tracks"] = playlist["tracks"]

        # noinspection PyTypeChecker
        for playlist in self.playlists:
            if playlist["id"] == iid:
                playlist_tracks = playlist["tracks"]
                if playlist["type"] == "Automatic":
                    self.filtered_library = playlist_tracks
                else:
                    self.filtered_library = self.songs_from_playlist(playlist_tracks)
                self.communicationqueue.put({"search results": True})
                return
        self.current_displayed_content_type = "Playlist"
        self.communicationqueue.put({"error":
                                         {"title": "Could not fetch playlist",
                                          "body": ":("}})
    def songs_from_playlist(self, playlist):
        tracks = list()
        for id_dict in playlist:
            if "track" in id_dict:
                track = id_dict["track"]
            else:
                track = next(filter(lambda t: t["id"] == id_dict['trackId'], self.library), None)
            if "id" not in track:
                track["id"] = track["storeId"]
            tracks.append(track)
        return tracks

    def play_song(self, trackid):
        try:
            import vlc
            if isinstance(trackid, dict):
                print('playing track', trackid['title'])
                trackid = trackid["id"]
            if trackid is None and self.player is not None:
                self.player.pause()
                return
            url = self.api.get_stream_url(trackid)
            if self.player is None:
                self.player = vlc.MediaPlayer(url) # type: vlc.MediaPlayer
            else:
                # TODO: this is terrible and I should fix it. Lucky it works!
                self.player = vlc.MediaPlayer(url)
            self.player.play()
            self.player.event_manager().event_attach(vlc.EventType.MediaPlayerEndReached, self.song_complete, trackid)
        except ImportError:
            self.communicationqueue.put({"error":
                                             {"title": "Could not import VLC",
                                              "body": "Please make sure you have 64-bit VLC installed"}})

    @callbackmethod
    def song_complete(self, event, trackId):
        if self.current_displayed_content_type == "Track":
            libiterator = iter(self.filtered_library)
            for track in libiterator:
                if track["id"] == trackId:
                    self.play_song(next(libiterator, None))
                    return

