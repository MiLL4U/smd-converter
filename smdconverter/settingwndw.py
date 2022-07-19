from copy import deepcopy
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

        # grid settings
        self.columnconfigure(0, weight=1)

        # variables
        # **settings are updated only when __handle_cancel_btn() is called**
        self.__current_settings = settings
        self.__new_settings = deepcopy(settings)

        self.__create_widgets()
        self.grab_set()  # make this window modal
        self.transient()  # Disable this window on the taskbar
        self.resizable(False, False)

    def __create_widgets(self) -> None:
        self.general_frame = GeneralSettingsFrame(self, self.__new_settings)
        self.general_frame.grid(
            row=0, column=0, sticky=tk.NSEW, **PADDING_OPTIONS)

        self.okcancel_btns = OKCancelButtonArray(
            self, self.__handle_ok_btn, self.__handle_cancel_btn)
        self.okcancel_btns.grid(
            row=2, column=0, sticky=tk.EW, **PADDING_OPTIONS)

    def __handle_ok_btn(self) -> None:
        self.__current_settings.overwrite_settings(self.__new_settings)
        self.__current_settings.save()
        self.destroy()

    def __handle_cancel_btn(self) -> None:
        self.destroy()


class GeneralSettingsFrame(ttk.LabelFrame):
    def __init__(self, master: tk.Misc, settings: ApplicationSettings,
                 *args, **kwargs) -> None:
        kwargs['master'] = master
        super().__init__(text="General Settings", *args, **kwargs)
        self.__settings = settings

        # variables
        self.__multi_job_flag = tk.BooleanVar(
            value=settings.multi_jobs_flag)
        self.__clear_jobs_flag = tk.BooleanVar(
            value=settings.clear_jobs_flag)

        self.__create_widgets()

    def __create_widgets(self) -> None:
        self.multi_job_chkbox = ttk.Checkbutton(
            self, command=self.__update_settings,
            text="Add multiple jobs when multiple detectors are found",
            variable=self.__multi_job_flag)
        self.multi_job_chkbox.grid(
            row=0, column=0, sticky=tk.W, **PADDING_OPTIONS)

        self.clear_jobs_chkbox = ttk.Checkbutton(
            self, command=self.__update_settings,
            text="Clear all jobs when comversion is complete",
            variable=self.__clear_jobs_flag)
        self.clear_jobs_chkbox.grid(
            row=1, column=0, sticky=tk.W, **PADDING_OPTIONS)

    def __update_settings(self) -> None:
        self.__settings.set_multi_jobs_flag(self.__multi_job_flag.get())
        self.__settings.set_clear_jobs_flag(self.__clear_jobs_flag.get())
