import pygubu
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from functools import partial
from main import Application


class Mainwindow(pygubu.TkApplication):
    def __init__(self, application: Application, master: tk.Tk = None):
        super().__init__(master)
        self.application = application

    def _create_ui(self):
        master = self.master
        master.wm_minsize(width=600, height=400)
        self.builder = builder = pygubu.Builder()
        master.rowconfigure(0, weight=1)
        master.columnconfigure(0, weight=1)
        builder.add_from_file('mainwindow.ui')
        self.mainwindow = mainwindow = builder.get_object('mainwindow', master)
        mainwindow.rowconfigure(4, weight=1)
        mainwindow.columnconfigure(1, weight=1)
        mainwindow.columnconfigure(0, weight=0)
        self.__treeview = builder.get_object('music_treeview')  # type: ttk.Treeview
        self.__loggedinlabel = builder.get_variable('loggedinlabel')  # type: tk.StringVar

        sortcallbacks = {'sort_title' : lambda: self.application.sort('title'),
                         'sort_artist': lambda: self.application.sort('artist'),
                         'sort_album': lambda: self.application.sort('album'),
                         'sort_saved': lambda: self.application.sort('saved')}

        builder.connect_callbacks(self)
        builder.connect_callbacks(sortcallbacks)

    def view_downloads(self):
        messagebox.showinfo("Test", "Text")

    def search_entry_changed(self, action: int, value: str):
        self.application.got_search_query(value)
        return True

    def download_selection(self):
        # returns a tuple of the iids of the selected items
        selected_items = self.__treeview.selection()  # type: tuple
        self.application.download_selection(selected_items)

    def insert_tracks(self, tracks):
        for track in tracks:
            self.__treeview.insert("", tk.END, track["id"], text="F",
                               values=(track["title"], track["artist"], track["album"], track["saved"]))

    def clear_tracks(self):
        self.__treeview.delete(*self.__treeview.get_children())

    def track_download_complete(self, track: dict):
        self.__treeview.set(track["id"], column="downloadedColumn", value="√")

    def display_loggedin_user(self, user: str):
        self.__loggedinlabel.set("Logged in as " + user)


