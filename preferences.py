import pygubu
import tkinter as tk
from tkinter import messagebox
from tkinter import Event
from pygubu.builder.widgets import pathchooserinput
import configparser
import platform
from main import Application


class Preferences():

    def __init__(self, master: tk.Toplevel, application: Application):

        self.master = master
        self.application = application
        self.builder = builder = pygubu.Builder()

        #2: Load an ui file
        builder.add_from_file('preferences.ui')

        #3: Create the widget using a master as parent
        self.mainwindow = builder.get_object('preferenceswindow', master)

        self.pathchooser = builder.get_object('musicfolder_chooser') # type: pathchooserinput

        self.__username_entry = builder.get_variable('username_entry')  # type: tk.StringVar
        self.__password_entry = builder.get_variable('password_entry')  # type: tk.StringVar

        builder.connect_callbacks(self)

        self.config = configparser.ConfigParser()
        self.config.read("config.ini")
        self.load_settings(self.config)

        if platform.system() == "Windows":
            self.master.attributes('-topmost', True)


    def load_settings(self, config: configparser.ConfigParser):
        try:
            self.account = config["Account"]
            self.__username_entry.set(self.account["username"])
            self.__password_entry.set(self.account["password"])

            self.settings = config["Settings"]
            self.pathchooser.configure(path=self.settings["music_directory"])
        except KeyError as e:
            pass
        # self.file_type = "." + self.settings["file_type"]
        # self.chunk_size = self.settings.getint("chunk_size")
        # self.max_threads = self.settings.getint("download_threads", 5)
        # self.gui_enabled = self.settings.getboolean("gui_enabled")

    def ok(self):
        self.write_settings()
        self.master.destroy()

    def cancel(self):
        self.master.destroy()

    def musicfolder_chosen(self, event):
        # messagebox.showinfo("You Chose", self.pathchooser.cget('path') + "\n")
        pass

    def write_settings(self):
        self.account["username"] = self.__username_entry.get()
        self.account["password"] = self.__password_entry.get()
        self.settings["music_directory"] = self.pathchooser.cget('path')
        with open('config.ini', 'w') as configfile:
            self.config.write(configfile)
        self.application.reload_settings(self.config)

