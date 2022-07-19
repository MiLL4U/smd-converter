import tkinter as tk
from tkinter import ttk

from .constants import PADDING_OPTIONS
from .appsettings import ApplicationSettings
from .okcancelbuttonarray import OKCancelButtonArray


class SettingsWindow(tk.Toplevel):
    # TODO: implement settings window
    def __init__(self, master: tk.Misc, settings: ApplicationSettings,
                 *args, **kwargs):
        kwargs['master'] = master
        super().__init__(*args, **kwargs)

        self.title("Settings")

        self.columnconfigure(0, weight=1)

        self.__create_widgets()
        self.grab_set()  # make this window modal
        self.transient()  # Disable this window on the taskbar
        self.resizable(False, False)

        # variables
        self.__settings = settings

    def __create_widgets(self) -> None:
        self.general_frame = GeneralSettingsFrame(self)
        self.general_frame.grid(
            row=0, column=0, sticky=tk.NSEW, **PADDING_OPTIONS)

        self.okcancel_btns = OKCancelButtonArray(
            self, self.__handle_ok_btn, self.__handle_cancel_btn)
        self.okcancel_btns.grid(
            row=2, column=0, sticky=tk.EW, **PADDING_OPTIONS)

    def __handle_ok_btn(self) -> None:
        print("ok")

    def __handle_cancel_btn(self) -> None:
        self.destroy()


class GeneralSettingsFrame(ttk.LabelFrame):
    def __init__(self, master: tk.Misc,
                 *args, **kwargs) -> None:
        kwargs['master'] = master
        super().__init__(text="General Settings", *args, **kwargs)

        self.__create_widgets()

    def __create_widgets(self) -> None:
        self.multi_job_chkbox = ttk.Checkbutton(
            self, text="Add multiple jobs when multiple detectors are found")
        self.multi_job_chkbox.grid(
            row=0, column=0, sticky=tk.W, **PADDING_OPTIONS)

        self.clear_jobs_chkbox = ttk.Checkbutton(
            self, text="Clear all jobs when comversion is complete")
        self.clear_jobs_chkbox.grid(
            row=1, column=0, sticky=tk.W, **PADDING_OPTIONS)
