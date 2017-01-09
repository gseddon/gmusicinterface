import pygubu
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

from main import Application


class Mainwindow(pygubu.TkApplication):
    def __init__(self, application: Application, master: tk.Tk =None):
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
        self.treeview = builder.get_object('music_treeview')  # type: ttk.Treeview
        self.loggedinlabel = builder.get_variable('loggedinlabel') # type: tk.StringVar
        builder.connect_callbacks(self)


    def view_downloads(self):
        messagebox.showinfo("Test", "Text")


    def get_variables(self):
        return {"searchbartext": self.builder.get_object("search_entry").get,
                "tableview": self.mainwindow}

    def search_entry_changed(self, action, value):
        self.application.got_search_query(value)
        return True

    def download_selection(self):
        # returns a tuple of the ids of the selected items
        selected_items = self.treeview.selection()  #type: tuple
        self.application.download_selection(selected_items)

    def insert_track(self, track: dict):
        self.treeview.insert("", tk.END, track["id"], text="F",
                                        values=(track["title"], track["artist"], track["album"], track["saved"]))

    def track_download_complete(self, track: dict):
        self.treeview.set(track["id"], column="downloadedColumn", value="√")
