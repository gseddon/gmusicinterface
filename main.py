from gmusicapi import Mobileclient
import configparser

import vlc


class Test():
    p = None
    def __init__(self):
        api = Mobileclient()
        print("initialised")
        api.login('gareth.seddon@gmail.com', 'pmzk993ne', Mobileclient.FROM_MAC_ADDRESS)
        print("logged in")
        library = api.get_all_songs()
        sweet_track_ids = [track for track in library if track['artist'] == 'Flume']

        id = sweet_track_ids[0]["id"]

        url = api.get_stream_url(id)
        print(sweet_track_ids[0]["artist"] + "\n" + url)
        self.instance = vlc.Instance(url)
        # self.p = vlc.MediaPlayer(url)
        # self.p.play()
        self.instance.media_player_new().play



if __name__ == "__main__":
    # test = Test()
    config = configparser.ConfigParser()
    config.read("account.ini")
    account = config["Account"]
    print(account["username"] + ", " + account["password"])
