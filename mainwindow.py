import pygubu
import tkinter as tk
from tkinter import messagebox
class Mainwindow(pygubu.TkApplication):
    def _create_ui(self):
        master = self.master
        self.builder = builder = pygubu.Builder()
        builder.add_from_file('mainwindow.ui')
        self.mainwindow = mainwindow = builder.get_object('mainwindow', master)
        master.rowconfigure(0, weight=1)
        master.columnconfigure(0, weight=1)
        # mainwindow.rowconfigure(4, weight=1)
        # mainwindow.columnconfigure(0, weight=1)
        builder.get_object('music_treeview').rowconfigure(1, weight=4)
        builder.connect_callbacks(self)

    def _init_before(self):
        tk.Frame = tk.LabelFrame

    def view_downloads(self):
        messagebox.showinfo("Test", "Text")