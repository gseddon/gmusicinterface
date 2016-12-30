from gmusicapi import Mobileclient
import configparser
import vlc




if __name__ == "__main__":
    config = configparser.ConfigParser()
    config.read("account.ini")
    account = config["Account"]
    api = Mobileclient()
    print("initialised", account["username"], account["password"])
    api.login(account["username"], account["password"], Mobileclient.FROM_MAC_ADDRESS)
    print("logged in")
    library = api.get_all_songs()
    sweet_track_ids = [track for track in library if track['artist'] == 'Flume']

    id = sweet_track_ids[0]["id"]

    url = api.get_stream_url(id)
    print(sweet_track_ids[0]["artist"] + "\n" + url)
    instance = vlc.Instance("--sout=#duplicate{dst=file{dst=example.mpg},dst=display}")
    media = instance.media_new(url)
    player = instance.media_player_new()
    player.set_media(media)
    player.play()

    # self.p = vlc.MediaPlayer(url)
    # self.p.play()

