import os

from gmusicapi import Mobileclient
import configparser
import requests
import vlc




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

    track_url = api.get_stream_url(tracks[0]['id'])
    r = requests.get(track_url)
    print("got request")
    with open("song.mp3", "wb") as binfile:
        binfile.write(bytearray(r.content))



    # if not os.path.exists(artist):
    #     os.makedirs(artist)
    # for album in [track['album'] for track in tracks]:
    #     albumpath = os.path.join(artist, album)
    #     if not os.path.exists(albumpath):
    #         os.makedirs(albumpath)
    # for track in tracks:
    #     track_url = api.get_stream_url(track['id'])
    #     trackpath = os.path.join(track['artist'], track['album'], track['title'])
    #     print(trackpath)
        # instance = vlc.Instance("--sout=file/ps:\"\'" + trackpath + ".mp3\'\"")
        # player = instance.media_player_new(track_url)
        # player.play()



    # self.p = vlc.MediaPlayer(url)
    # self.p.play()

