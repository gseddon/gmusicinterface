import pygubu
import tkinter as tk
from tkinter import messagebox
from tkinter import Event
from pygubu.builder.widgets import pathchooserinput

class Preferences():

    def __init__(self, master):

        self.master = master
        self.builder = builder = pygubu.Builder()

        #2: Load an ui file
        builder.add_from_file('preferences.ui')

        #3: Create the widget using a master as parent
        self.mainwindow = builder.get_object('preferenceswindow', master)

        self.pathchooser = builder.get_object('musicfolder_chooser') # type: pathchooserinput

        self.__username_entry = builder.get_variable('username_entry')  # type: tk.StringVar
        self.__password_entry = builder.get_variable('password_entry')  # type: tk.StringVar
        self.__music_path = self.pathchooser.cget('path')

        builder.connect_callbacks(self)

    def ok(self):
        self.write_setttings()
        self.master.destroy()

    def cancel(self):
        self.master.destroy()

    def musicfolder_chosen(self, event):
        messagebox.showinfo("You Chose", self.pathchooser.cget('path') + "\n")

    def write_setttings(self):
        pass

