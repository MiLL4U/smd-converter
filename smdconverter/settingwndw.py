import tkinter as tk
from copy import deepcopy
from tkinter import ttk
from typing import Dict, cast

from .appsettings import ApplicationSettings
from .constants import (PADDING_OPTIONS, SPECTRAL_AXIS_FORMAT_COLUMN_TEXTS,
                        SPECTRAL_AXIS_FORMAT_COLUMNS,
                        SPECTRAL_DATA_FORMAT_COLUMN_TEXTS,
                        SPECTRAL_DATA_FORMAT_COLUMNS)
from .defaultsettings import DEFAULT_SETTINGS
from .editabletree import ChangeableTreeFrame, EditableTreeFrame
from .okcancelbuttonarray import OKCancelButtonArray

TREE_HEIGHT = 5
DIALOG_TITLE = "Edit name format"
ENTRY_LENGTH = 30
EMPTY_OK = False


class SettingsWindow(tk.Toplevel):
    def __init__(self, master: tk.Misc, settings: ApplicationSettings,
                 *args, **kwargs):
        kwargs['master'] = master
        super().__init__(*args, **kwargs)

        self.title("Settings")

        # grid settings
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)  # general settings
        self.rowconfigure(1, weight=1)  # name format for spectral data
        self.rowconfigure(2, weight=1)  # name format for spectral axis
        self.rowconfigure(3, weight=0)  # ok and cancel buttons

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
            column=0, row=0, sticky=tk.NSEW, **PADDING_OPTIONS)

        self.data_fmt_frame = DataFormatTreeFrame(
            master=self, columns=SPECTRAL_DATA_FORMAT_COLUMNS,
            column_texts=SPECTRAL_DATA_FORMAT_COLUMN_TEXTS,
            values_dict=self.__new_settings.data_name_formats,
            height=5, text="Wave name format (spectral data)")
        self.data_fmt_frame.grid(
            column=0, row=1, sticky=tk.EW, **PADDING_OPTIONS)

        default_axis_fmt = DEFAULT_SETTINGS['spectralAxisNameFormats']
        default_axis_fmt = cast(Dict[str, str], default_axis_fmt)
        self.axis_fmt_frame = AxisFormatTreeFrame(
            master=self, columns=SPECTRAL_AXIS_FORMAT_COLUMNS,
            column_texts=SPECTRAL_AXIS_FORMAT_COLUMN_TEXTS,
            values_dict=self.__new_settings.spectral_axis_name_formats,
            default_values=default_axis_fmt,
            height=5, text="Wave name format (spectral axis)")
        self.axis_fmt_frame.grid(
            column=0, row=2, sticky=tk.EW, **PADDING_OPTIONS)

        self.okcancel_btns = OKCancelButtonArray(
            master=self, ok_command=self.__handle_ok_btn,
            cancel_command=self.__handle_cancel_btn)
        self.okcancel_btns.grid(
            column=0, row=3, sticky=tk.EW)

    def __handle_ok_btn(self) -> None:
        self.__current_settings.overwrite_settings(self.__new_settings)
        self.__current_settings.save()
        print("Information: Settings have been changed.")
        self.destroy()

    def __handle_cancel_btn(self) -> None:
        print("Information: The change of settings is canceled.")
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
            column=0, row=0, sticky=tk.W, **PADDING_OPTIONS)

        self.clear_jobs_chkbox = ttk.Checkbutton(
            self, command=self.__update_settings,
            text="Clear all jobs when comversion is completed",
            variable=self.__clear_jobs_flag)
        self.clear_jobs_chkbox.grid(
            column=0, row=1, sticky=tk.W, **PADDING_OPTIONS)

    def __update_settings(self) -> None:
        self.__settings.set_multi_jobs_flag(self.__multi_job_flag.get())
        self.__settings.set_clear_jobs_flag(self.__clear_jobs_flag.get())


class DataFormatTreeFrame(EditableTreeFrame):
    def __init__(self, master: tk.Misc, values_dict: Dict[str, str],
                 *args, **kwargs):
        kwargs['master'] = master
        kwargs['columns'] = SPECTRAL_DATA_FORMAT_COLUMNS
        kwargs['column_texts'] = SPECTRAL_DATA_FORMAT_COLUMN_TEXTS
        kwargs['values_dict'] = values_dict
        kwargs['height'] = TREE_HEIGHT
        kwargs['changeable_flags'] = (True, True)
        kwargs['dialog_title'] = DIALOG_TITLE
        kwargs['entry_length'] = ENTRY_LENGTH
        kwargs['empty_ok'] = EMPTY_OK
        super().__init__(*args, **kwargs)


class AxisFormatTreeFrame(ChangeableTreeFrame):
    def __init__(self, master: tk.Misc, values_dict: Dict[str, str],
                 *args, **kwargs):
        kwargs['master'] = master
        kwargs['columns'] = SPECTRAL_AXIS_FORMAT_COLUMNS
        kwargs['column_texts'] = SPECTRAL_AXIS_FORMAT_COLUMN_TEXTS
        kwargs['values_dict'] = values_dict
        kwargs['height'] = TREE_HEIGHT
        kwargs['changeable_flags'] = (False, True)
        kwargs['dialog_title'] = DIALOG_TITLE
        kwargs['entry_length'] = ENTRY_LENGTH
        kwargs['empty_ok'] = EMPTY_OK
        super().__init__(*args, **kwargs)
