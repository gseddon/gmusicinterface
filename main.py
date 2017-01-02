import os

import sys
from gmusicapi import Mobileclient
import configparser
import requests
import vlc

chunk_size = 4096
is_stream = True

def create_dir(track):
    artist = track["artist"]
    album = track["album"]
    albumpath = os.path.join(artist, album)
    if not os.path.exists(albumpath):
        os.makedirs(albumpath)
    return albumpath

def stream_download(track):
    track_url = api.get_stream_url(track['id'])
    track_title = track["title"]
    response = requests.get(track_url, stream=True)
    print("downloading " + track_title, end="")
    total_length = int(response.headers.get('content-length'))
    dl = 0
    with open(os.path.join(create_dir(track), track_title + ".mp3"), "wb") as songfile:
        for chunk in response.iter_content(chunk_size=chunk_size):
            songfile.write(chunk)
            dl += len(chunk)
            print(".", end="")
    print(" done.")






if __name__ == "__main__":
    config = configparser.ConfigParser()
    config.read("account.ini")
    account = config["Account"]
    api = Mobileclient()
    print("initialised")
    api.login(account["username"], account["password"], Mobileclient.FROM_MAC_ADDRESS)
    print("logged in")
    library = api.get_all_songs()
    artist = 'Flume'
    tracks = [track for track in library if track['artist'] == artist]

    # track_url = api.get_stream_url(tracks[0]['id'])
    stream_download(tracks[0])
