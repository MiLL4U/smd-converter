import tkinter as tk
from tkinter import ttk

from .appsettings import ApplicationSettings


class SettingsWindow(tk.Toplevel):
    # TODO: implement settings window
    def __init__(self, master: tk.Misc, settings: ApplicationSettings,
                 *args, **kwargs):
        kwargs['master'] = master
        super().__init__(*args, **kwargs)

        self.title("Sub window")
        self.geometry("300x300")
        self.__create_widgets()
        self.grab_set()  # make this window modal
        self.transient(self.master)  # Disable this window on the taskbar

        # variables
        self.__settings = settings

    def __create_widgets(self):
        self.close_btn = ttk.Button(
            self, text="Close sub window",
            command=self.__handle_close_btn)
        self.close_btn.pack()

    def __handle_close_btn(self):
        self.destroy()
