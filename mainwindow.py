import pygubu
import tkinter as tk
from tkinter import messagebox
class Mainwindow(pygubu.TkApplication):
    def _create_ui(self):
        master = self.master
        self.builder = builder = pygubu.Builder()
        master.rowconfigure(0, weight=1)
        master.columnconfigure(0, weight=1)
        builder.add_from_file('mainwindow.ui')
        self.mainwindow = mainwindow = builder.get_object('mainwindow', master)
        mainwindow.rowconfigure(4, weight=1)
        mainwindow.columnconfigure(1, weight=1)
        mainwindow.columnconfigure(0, weight=0)
        builder.get_object('music_treeview')
        builder.connect_callbacks(self)


    def view_downloads(self):
        messagebox.showinfo("Test", "Text")

