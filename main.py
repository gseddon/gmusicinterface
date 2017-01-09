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
            self.window = window = Mainwindow(self, guiroot)
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
            except Empty:
                pass
        self.guiroot.after(100, self.poll_downloader)

    def got_search_query(self, query):
        print("downloader ", query)
        if self.gui_enabled:
            # we need to only remove those songs which aren't there any more, and add new songs.
            # oldtrackids = set([track['id'] for track in self.tracks])
            # self.tracks = [track for track in self.library if track['artist'] == query]
            # updatedtrackids = set([track['id'] for track in self.tracks])
            # intersection = oldtrackids & updatedtrackids
            # deletetrackids = oldtrackids - intersection
            # newtrackids = updatedtrackids - intersection
            # if len(deletetrackids) > 0:
            #     self.window.treeview.delete(list(deletetrackids))
            # for track in (track for track in self.tracks if track["id"] in newtrackids):
            #     self.window.treeview.insert("", tk.END, track["id"], text="F", values= ( track["title"], track["artist"], track["album"]))
            self.window.treeview.delete(*self.window.treeview.get_children())
            self.tracks = self.downloader.library
            for track in self.tracks:
                if self.downloader.track_already_downloaded(track):
                   saved = "√"
                else:
                    saved = ""
                self.window.treeview.insert("", tk.END, track["id"], text="F",
                                        values=(track["title"], track["artist"], track["album"], saved))
        else:
            print([track["title"] for track in self.library if track['artist'] in query])



    def login_complete(self, username):
        self.window.loggedinlabel.set("Logged in as " + username)



    def load_settings(self, settingsDict):
        self.gui_enabled = settingsDict.getboolean("gui_enabled")


if __name__ == "__main__":
    Application()