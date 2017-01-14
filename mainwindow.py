import pygubu
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from functools import partial
from main import Application

from preferences import Preferences


class Mainwindow(pygubu.TkApplication):

    treeview_contenttype = "Track"
    message = None

    def __init__(self, application: Application, master: tk.Tk = None):
        super().__init__(master)
        self.application = application

    def _create_ui(self):
        master = self.master
        master.wm_minsize(width=600, height=400)
        master.wm_title("GMusic Downloader")

        self.builder = builder = pygubu.Builder()
        master.rowconfigure(0, weight=1)
        master.columnconfigure(0, weight=1)
        builder.add_from_file('mainwindow.ui')
        self.mainwindow = mainwindow = builder.get_object('mainwindow', master)
        self.mainmenu = menu = builder.get_object('mainmenu')
        self.set_menu(menu)

        mainwindow.rowconfigure(4, weight=1)
        mainwindow.columnconfigure(1, weight=1)
        mainwindow.columnconfigure(0, weight=0)
        self.__treeview = builder.get_object('music_treeview')                          # type: ttk.Treeview
        self.__loggedinlabel = builder.get_variable('loggedinlabel')                    # type: tk.StringVar
        self.__currentdownloadslabel = builder.get_variable('currentdownloadslabel')    # type: tk.StringVar
        self.__downloadcountlabel = builder.get_variable('downloadcountlabel')          # type: tk.StringVar
        self.__searchentry = builder.get_variable('searchentry')                        # type: tk.StringVar

        callbacks = {'sort_title' :         lambda: self.application.sort('title', self.treeview_contenttype),
                         'sort_artist':     lambda: self.application.sort('artist', self.treeview_contenttype),
                         'sort_album':      lambda: self.application.sort('album', self.treeview_contenttype),
                         'sort_saved':      lambda: self.application.sort('saved', self.treeview_contenttype),
                         'search_gmusic':   lambda: self.application.search_gmusic(self.__searchentry.get()),
                         'search_entry_enter_pressed': lambda b: self.application.search_gmusic(self.__searchentry.get()),
                         'search_entry_changed': lambda a, v: self.application.got_search_query(v),
                         'open_playlists': lambda: self.application.open_playlists(),
                         'download_selection': lambda:  self.application.download_selection(self.__treeview.selection()),
                         'open_preferences' : lambda: self.open_preferences(),
                         'ontreeview_doubleclick': lambda e: self.ontreeview_doubleclick(e)
                     }

        builder.connect_callbacks(callbacks)

    def view_downloads(self):
        messagebox.showinfo("Test", "Text")

    def insert_tracks(self, tracks):
        self.configure_treeview_for_content("Track")
        for track in tracks:
            if not self.__treeview.exists(track["id"]):
                self.__treeview.insert("", tk.END, track["id"], text="T",
                               values=(track["title"], track["artist"], track["album"], track["saved"]))
            else:
                self.__treeview.move(track["id"], "", tk.END)

    def empty_treeview(self):
        self.__treeview.delete(*self.__treeview.get_children())

    def track_download_complete(self, track: dict):
        self.__treeview.set(track["id"], column="downloadedColumn", value="√")
        self.update_current_downloads(track["title"], remove=True)

    def display_loggedin_user(self, user: str):
        self.__loggedinlabel.set("Logged in as " + user)

    def open_preferences(self):
        self.newwindow = tk.Toplevel(self.master)
        self.newwindow.wm_title("Preferences")
        self.preferences = Preferences(self.newwindow, self.application)

    def update_current_downloads(self, tracktitle: str, remove: bool = False):
        currentstring = self.__currentdownloadslabel.get()
        if not remove:
            if currentstring == "":
                self.__currentdownloadslabel.set("Downloading: " + tracktitle)
            else:
                self.__currentdownloadslabel.set(currentstring + ", " + tracktitle)
        else:
            updated = currentstring.replace(", " + tracktitle, "", 1)
            updated = updated.replace("Downloading: " + tracktitle, "")
            if (updated.startswith(", ")):
                updated = updated.replace(", ", "Downloading: ", 1)
            self.__currentdownloadslabel.set(updated)

    def update_download_count(self, current=0, total=0, complete=False):
        if complete:
            self.__downloadcountlabel.set("")
        else:
            self.__downloadcountlabel.set("{}/{} @ n kb/s".format(current, total) )

    def update_user_with_error(self, error: dict):
        messagebox.showerror(error["title"], error["body"])

    def display_playlists(self, playlists: dict):
        self.empty_treeview()
        self.configure_treeview_for_content("Playlist")
        for playlist in playlists:
            if not 'type' in playlist or playlist['type'] == 'USER_GENERATED':
                playlist['type'] = 'User'
            self.__treeview.insert("", tk.END, playlist["id"], text="P", values=(playlist["name"], playlist["ownerName"], playlist['type']))

    def configure_treeview_for_content(self, content_type):
        if content_type is "Playlist":
            self.__treeview.heading(column="artistcolumn", text="Playlist Owner")
            self.__treeview.heading(column="albumcolumn", text="Playlist Type")
        elif content_type is "Track":
            self.__treeview.heading(column="artistcolumn", text="Artist")
            self.__treeview.heading(column="albumcolumn", text="Album")
        self.treeview_contenttype = content_type

    def ontreeview_doubleclick(self, event):
        item = self.__treeview.identify('item', event.x, event.y)
        print('displaying playlist', item)
        if self.treeview_contenttype is "Playlist":
            self.application.display_playlist(item)

    def working(self, message="", remove=False):
        currentstring = self.__currentdownloadslabel.get()
        if self.message is not None:
            currentstring = currentstring.replace(self.message, "")
        self.message = message
        if remove:
            self.__currentdownloadslabel.set(currentstring)
        else:
            self.__currentdownloadslabel.set(currentstring + message)
