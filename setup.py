from cx_Freeze import setup,Executable
import os
#  http://stackoverflow.com/questions/13862562/google-protocol-buffers-not-found-when-trying-to-freeze-python-app

os.environ['TCL_LIBRARY'] = "C:\\Anaconda3\\tcl\\tcl8.6"
os.environ['TK_LIBRARY'] = "C:\\Anaconda3\\tcl\\tk8.6"

includefiles = ['config.ini',
                r"C:\Anaconda3\DLLs\tcl86t.dll",
                r"C:\Anaconda3\DLLs\tk86t.dll",
                'mainwindow.ui',
                'preferences.ui']
packages = ['tkinter', 'gmusicapi','requests', 'pygubu', 'mutagen']

setup(
    name = 'GMusicDownloader',
    version = '0.1',
    description = 'A utility to access music files from google play music',
    author = 'G',
    author_email = 'no@dice',
    options = {'build_exe': {'packages':packages,'include_files':includefiles}},
    executables=[Executable("main.py", base="Win32GUI")])





